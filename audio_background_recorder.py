#!/usr/bin/env python3
"""
Background Audio Recording and Transcription Service
Automatically detects and records system audio (like Zoom calls) and stores transcripts in ChromaDB.
Designed to run as a background service alongside the Flow system.
Uses OpenAI Whisper API for transcription and stores data as markdown files.
"""

import os
import sys
import time
import threading
import queue
import signal
import subprocess
import logging
from datetime import datetime
from pathlib import Path
import json
import argparse
from typing import Dict, Any, Optional
import tempfile

import numpy as np
from openai import OpenAI
import chromadb
from chromadb.errors import ChromaError
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('audio_background.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BackgroundAudioRecorder:
    def __init__(self, 
                 output_dir="refinery/data/audio", 
                 chunk_duration=30,
                 silence_threshold=0.01,
                 min_recording_duration=10,
                 chroma_host="localhost",
                 chroma_port=8000):
        """
        Initialize the background audio recorder.
        
        Args:
            output_dir: Directory to save audio and transcription files
            chunk_duration: Duration in seconds for each audio chunk to transcribe
            silence_threshold: Audio level below which is considered silence
            min_recording_duration: Minimum duration to keep a recording
            chroma_host: ChromaDB host
            chroma_port: ChromaDB port
        """
        # Load environment variables for OpenAI API key
        load_dotenv()
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.chunk_duration = chunk_duration
        self.silence_threshold = silence_threshold
        self.min_recording_duration = min_recording_duration
        self.is_running = False
        self.is_recording = False
        self.audio_queue = queue.Queue()
        
        # ChromaDB settings
        self.chroma_host = chroma_host
        self.chroma_port = chroma_port
        self.chroma_client = None
        
        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in .env file")
        
        self.openai_client = OpenAI(api_key=api_key)
        logger.info("OpenAI client initialized successfully!")
        
        # Session info
        self.current_session = None
        self.session_data = {}
        
        # Audio detection
        self.audio_buffer = []
        self.last_audio_time = None
        self.recording_start_time = None
        
    def init_chroma(self):
        """Initialize ChromaDB connection."""
        try:
            self.chroma_client = chromadb.HttpClient(
                host=self.chroma_host,
                port=self.chroma_port
            )
            
            # Test connection
            heartbeat = self.chroma_client.heartbeat()
            logger.info(f"ChromaDB connected to {self.chroma_host}:{self.chroma_port}")
            
            # Get or create the same collection as OCR data
            self.collection = self.chroma_client.get_or_create_collection(
                name="screen_ocr_history",
                metadata={"description": "Screen OCR and audio transcript data"}
            )
            logger.info("Using screen_ocr_history collection in ChromaDB")
            
        except Exception as e:
            logger.warning(f"ChromaDB connection failed: {e}")
            logger.warning("Audio will be saved locally but not stored in ChromaDB")
            self.chroma_client = None
    
    def detect_system_audio_method(self):
        """Detect the best method to capture both microphone and system audio on macOS."""
        try:
            # Check if BlackHole is installed (recommended virtual audio driver)
            result = subprocess.run(['system_profiler', 'SPAudioDataType'], 
                                  capture_output=True, text=True)
            if 'BlackHole' in result.stdout:
                logger.info("BlackHole virtual audio driver detected")
                logger.info("Will capture BOTH microphone and system audio (YouTube, Zoom, etc.)")
                return "blackhole"
            
            # Check if SoundFlower is available
            if 'Soundflower' in result.stdout:
                logger.info("Soundflower virtual audio driver detected")
                logger.info("Will capture BOTH microphone and system audio")
                return "soundflower"
            
            # Fall back to using ffmpeg - microphone only without BlackHole
            if subprocess.run(['which', 'ffmpeg'], capture_output=True).returncode == 0:
                logger.warning("Using ffmpeg for microphone capture only")
                logger.warning("To also capture system audio (YouTube, Zoom, etc.), install BlackHole:")
                logger.warning("  brew install blackhole-2ch")
                logger.warning("  Then set up Multi-Output Device in Audio MIDI Setup")
                return "ffmpeg"
            
            logger.warning("No suitable audio capture method found")
            return None
            
        except Exception as e:
            logger.error(f"Error detecting audio method: {e}")
            return None
    
    def start_system_audio_capture(self):
        """Start capturing ALL audio (microphone + system audio) using the best available method."""
        method = self.detect_system_audio_method()
        
        if method == "ffmpeg":
            logger.info("Capturing microphone only (no BlackHole detected)")
            return self._start_ffmpeg_capture()
        elif method in ["blackhole", "soundflower"]:
            logger.info("Capturing BOTH microphone and system audio")
            return self._start_virtual_driver_capture(method)
        else:
            logger.error("No audio capture method available")
            logger.info("Install ffmpeg: brew install ffmpeg")
            logger.info("For complete audio capture, also install BlackHole:")
            logger.info("  brew install blackhole-2ch")
            return None
    
    def _start_ffmpeg_capture(self):
        """Start audio capture using ffmpeg - captures BOTH microphone and system audio."""
        try:
            # List available devices first for logging
            list_cmd = ['ffmpeg', '-f', 'avfoundation', '-list_devices', 'true', '-i', '']
            list_result = subprocess.run(list_cmd, capture_output=True, text=True)
            logger.debug(f"Available audio devices:\n{list_result.stderr}")
            
            # Capture both microphone (audio input) and system audio
            # Format: -i ":microphone_index" for mic, -i ":system_audio_index" for system
            # We'll use :0 for default microphone and try to detect system audio
            # 
            # For macOS with BlackHole or similar:
            # - Input device 0 is usually microphone
            # - You need BlackHole or similar for system audio capture
            #
            # This command captures microphone. For system audio, user needs BlackHole.
            # We'll create a multi-input setup that mixes both sources
            
            cmd = [
                'ffmpeg',
                '-f', 'avfoundation',
                # Capture both audio input (microphone at :0) and system audio
                # Format is "video_device:audio_device"
                # ":0" means no video, audio device 0 (microphone)
                # We'll use a more complex setup to capture multiple audio sources
                '-i', ':0',  # Microphone input
                # Note: To also capture system audio, you'll need BlackHole installed
                # and this will be mixed in a more advanced setup below
                '-ar', '44100',
                '-ac', '1',  # Mono
                '-f', 'wav',
                '-'  # Output to stdout
            ]
            
            # Check if we should try to capture system audio too
            # This requires BlackHole or Soundflower to be set up
            if self._has_blackhole_device():
                logger.info("BlackHole detected - will attempt to capture both mic and system audio")
                # Use a more complex ffmpeg command to mix both sources
                cmd = self._build_multi_source_command()
            else:
                logger.warning("BlackHole not detected - capturing microphone only")
                logger.info("To capture system audio, install BlackHole: brew install blackhole-2ch")
                logger.info("Then create a Multi-Output Device in Audio MIDI Setup")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0
            )
            
            logger.info("Started ffmpeg audio capture (microphone + system audio if available)")
            return process
            
        except Exception as e:
            logger.error(f"Failed to start ffmpeg capture: {e}")
            return None
    
    def _has_blackhole_device(self):
        """Check if BlackHole virtual audio device is installed."""
        try:
            result = subprocess.run(
                ['ffmpeg', '-f', 'avfoundation', '-list_devices', 'true', '-i', ''],
                capture_output=True,
                text=True
            )
            # ffmpeg outputs device list to stderr, not stdout
            output = (result.stdout + result.stderr).lower()
            return 'blackhole' in output
        except Exception as e:
            logger.debug(f"Error checking for BlackHole: {e}")
            return False
    
    def _build_multi_source_command(self):
        """Build ffmpeg command to capture and mix microphone + system audio."""
        # This captures from multiple audio sources and mixes them
        # Input 0: Microphone (default audio input)
        # Input 1: BlackHole (system audio routed through it)
        return [
            'ffmpeg',
            '-f', 'avfoundation',
            '-i', ':0',  # Microphone
            '-f', 'avfoundation', 
            '-i', ':BlackHole 2ch',  # System audio through BlackHole
            '-filter_complex', '[0:a][1:a]amix=inputs=2:duration=longest',  # Mix both audio sources
            '-ar', '44100',
            '-ac', '1',  # Mono
            '-f', 'wav',
            '-'  # Output to stdout
        ]
    
    def _start_virtual_driver_capture(self, driver_name):
        """Start audio capture using virtual audio driver to capture both mic and system audio."""
        logger.info(f"Using {driver_name} to capture microphone + system audio")
        # Use the multi-source ffmpeg command
        return self._start_ffmpeg_capture()
    
    def start_background_monitoring(self):
        """Start the background audio monitoring service."""
        logger.info("🎙️  Starting background audio monitoring...")
        self.is_running = True
        
        # Initialize ChromaDB
        self.init_chroma()
        
        # Start audio capture process
        self.audio_process = self.start_system_audio_capture()
        if not self.audio_process:
            logger.error("Failed to start audio capture")
            return False
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_audio)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        # Start transcription thread
        self.transcription_thread = threading.Thread(target=self._transcribe_audio)
        self.transcription_thread.daemon = True
        self.transcription_thread.start()
        
        logger.info("✅ Background audio monitoring started!")
        logger.info("🔍 Listening for audio activity...")
        return True
    
    def _monitor_audio(self):
        """Monitor audio stream for activity."""
        buffer_size = 4096
        
        while self.is_running:
            try:
                if not self.audio_process or self.audio_process.poll() is not None:
                    logger.warning("Audio process stopped, restarting...")
                    self.audio_process = self.start_system_audio_capture()
                    if not self.audio_process:
                        time.sleep(5)
                        continue
                
                # Read audio data
                audio_data = self.audio_process.stdout.read(buffer_size)
                if not audio_data:
                    continue
                
                # Convert to numpy array for analysis
                audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
                
                # Check audio level
                audio_level = np.max(np.abs(audio_np))
                
                if audio_level > self.silence_threshold:
                    # Audio detected
                    self.last_audio_time = time.time()
                    
                    if not self.is_recording:
                        # Start new recording session
                        self._start_recording_session()
                    
                    # Add to buffer
                    self.audio_buffer.extend(audio_data)
                
                elif self.is_recording:
                    # Check if we should stop recording (silence for too long)
                    if time.time() - self.last_audio_time > 5:  # 5 seconds of silence
                        self._stop_recording_session()
                
            except Exception as e:
                logger.error(f"Error in audio monitoring: {e}")
                time.sleep(1)
    
    def _start_recording_session(self):
        """Start a new recording session."""
        self.is_recording = True
        self.recording_start_time = datetime.now()
        session_id = f"auto_{self.recording_start_time.strftime('%Y%m%d_%H%M%S')}"
        
        # Files are saved directly in the audio data directory (no subdirectory per session)
        self.current_session = {
            "session_id": session_id,
            "start_time": self.recording_start_time.isoformat(),
            "audio_file": self.output_dir / f"{session_id}.wav",
            "markdown_file": self.output_dir / f"{session_id}.md",
            "json_file": self.output_dir / f"{session_id}.json",
            "transcript": []
        }
        
        self.audio_buffer = []
        logger.info(f"🔴 Started recording session: {session_id}")
    
    def _stop_recording_session(self):
        """Stop the current recording session."""
        if not self.is_recording or not self.current_session:
            return
        
        self.is_recording = False
        session_end = datetime.now()
        duration = session_end - self.recording_start_time
        
        # Check if recording is long enough to keep
        if duration.total_seconds() < self.min_recording_duration:
            logger.info(f"⏭️  Recording too short ({duration.total_seconds():.1f}s), discarding")
            return
        
        logger.info(f"🛑 Stopping recording session: {self.current_session['session_id']}")
        
        # Save audio file
        if self.audio_buffer:
            self._save_audio_file()
        
        # Process final transcript chunk
        if self.audio_buffer:
            timestamp = datetime.now()
            self.audio_queue.put((bytes(self.audio_buffer), timestamp, self.current_session))
        
        # Update session data
        self.current_session.update({
            "end_time": session_end.isoformat(),
            "duration": str(duration)
        })
        
        # Save session metadata
        self._save_session_data()
        
        logger.info(f"✅ Session completed: {duration.total_seconds():.1f}s, {len(self.current_session['transcript'])} transcripts")
        
        self.current_session = None
        self.audio_buffer = []
    
    def _save_audio_file(self):
        """Save the audio buffer to a WAV file."""
        try:
            import wave
            
            with wave.open(str(self.current_session['audio_file']), 'wb') as wf:
                wf.setnchannels(1)  # Mono
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(44100)
                wf.writeframes(bytes(self.audio_buffer))
            
            logger.debug(f"Audio saved: {self.current_session['audio_file']}")
            
        except Exception as e:
            logger.error(f"Error saving audio file: {e}")
    
    def _transcribe_audio(self):
        """Transcribe audio chunks in a separate thread using OpenAI Whisper API."""
        logger.info("🤖 Transcription thread started...")
        
        while self.is_running or not self.audio_queue.empty():
            try:
                # Get audio chunk from queue
                chunk_audio, timestamp, session = self.audio_queue.get(timeout=1.0)
                
                # Convert audio data to numpy array
                audio_np = np.frombuffer(chunk_audio, dtype=np.int16).astype(np.float32) / 32768.0
                
                # Skip if audio is too quiet
                if np.max(np.abs(audio_np)) < self.silence_threshold:
                    continue
                
                logger.info(f"🔍 Transcribing chunk from {timestamp.strftime('%H:%M:%S')}...")
                
                # Save audio to temporary WAV file for OpenAI API
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
                    import wave
                    with wave.open(temp_audio.name, 'wb') as wf:
                        wf.setnchannels(1)  # Mono
                        wf.setsampwidth(2)  # 16-bit
                        wf.setframerate(44100)
                        wf.writeframes(chunk_audio)
                    
                    temp_path = temp_audio.name
                
                # Transcribe with OpenAI Whisper API
                try:
                    with open(temp_path, 'rb') as audio_file:
                        result = self.openai_client.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file,
                            response_format="verbose_json"
                        )
                    
                    text = result.text.strip()
                    
                    if text:
                        # Add to session data
                        transcript_entry = {
                            "timestamp": timestamp.isoformat(),
                            "text": text,
                            "duration": result.duration if hasattr(result, 'duration') else 0.0
                        }
                        session["transcript"].append(transcript_entry)
                        
                        # Append to markdown file
                        with open(session['markdown_file'], 'a', encoding='utf-8') as f:
                            if len(session["transcript"]) == 1:
                                # First entry - write header
                                f.write(f"# Audio Transcript: {session['session_id']}\n\n")
                                f.write(f"**Session Start:** {session['start_time']}\n\n")
                                f.write("---\n\n")
                            
                            f.write(f"## [{timestamp.strftime('%H:%M:%S')}]\n\n")
                            f.write(f"{text}\n\n")
                        
                        # Store in ChromaDB
                        self._store_in_chroma(transcript_entry, session)
                        
                        logger.info(f"📝 [{timestamp.strftime('%H:%M:%S')}] {text}")
                
                finally:
                    # Clean up temporary file
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Transcription error: {e}")
                continue
    
    def _store_in_chroma(self, transcript_entry: Dict[str, Any], session: Dict[str, Any]):
        """Store transcript in ChromaDB in the screen_ocr_history collection with 'audio' tag."""
        if not self.chroma_client:
            return
        
        try:
            # Prepare content for embedding
            content = f"Audio transcript: {transcript_entry['text']}"
            
            # Prepare metadata with 'audio' data_type tag
            metadata = {
                "timestamp": transcript_entry["timestamp"],
                "session_id": session["session_id"],
                "source": "background_audio_recording",
                "data_type": "audio",  # Tag to differentiate from OCR
                "task_category": "audio_transcript",
                "text_length": len(transcript_entry['text']),
                "word_count": len(transcript_entry['text'].split()),
                "extracted_text": transcript_entry['text']
            }
            
            # Store in ChromaDB screen_ocr_history collection
            doc_id = f"audio_{session['session_id']}_{transcript_entry['timestamp'].replace(':', '-').replace('.', '-')}"
            
            self.collection.add(
                documents=[content],
                metadatas=[metadata],
                ids=[doc_id]
            )
            
            logger.debug(f"Stored in ChromaDB screen_ocr_history collection: {doc_id}")
            
        except Exception as e:
            logger.warning(f"ChromaDB storage failed: {e}")
    
    def _save_session_data(self):
        """Save session data to JSON file."""
        if not self.current_session:
            return
        
        try:
            with open(self.current_session['json_file'], 'w', encoding='utf-8') as f:
                json.dump(self.current_session, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            logger.error(f"Error saving session data: {e}")
    
    def stop_monitoring(self):
        """Stop the background monitoring service."""
        logger.info("🛑 Stopping background audio monitoring...")
        self.is_running = False
        
        # Stop current recording if active
        if self.is_recording:
            self._stop_recording_session()
        
        # Stop audio process
        if hasattr(self, 'audio_process') and self.audio_process:
            self.audio_process.terminate()
        
        # Wait for threads to finish
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join(timeout=5)
        if hasattr(self, 'transcription_thread'):
            self.transcription_thread.join(timeout=10)
        
        logger.info("✅ Background audio monitoring stopped")


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info("🛑 Received shutdown signal...")
    if 'recorder' in globals():
        recorder.stop_monitoring()
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="Background audio recording and transcription service")
    parser.add_argument("--output-dir", default="refinery/data/audio", 
                       help="Directory to save recordings (default: refinery/data/audio)")
    parser.add_argument("--chunk-duration", type=int, default=30,
                       help="Duration in seconds for transcription chunks (default: 30)")
    parser.add_argument("--silence-threshold", type=float, default=0.01,
                       help="Audio level threshold for silence detection (default: 0.01)")
    parser.add_argument("--min-duration", type=int, default=10,
                       help="Minimum recording duration in seconds (default: 10)")
    parser.add_argument("--chroma-host", default="localhost",
                       help="ChromaDB host (default: localhost)")
    parser.add_argument("--chroma-port", type=int, default=8000,
                       help="ChromaDB port (default: 8000)")
    
    args = parser.parse_args()
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Create recorder
        global recorder
        recorder = BackgroundAudioRecorder(
            output_dir=args.output_dir,
            chunk_duration=args.chunk_duration,
            silence_threshold=args.silence_threshold,
            min_recording_duration=args.min_duration,
            chroma_host=args.chroma_host,
            chroma_port=args.chroma_port
        )
        
        # Start monitoring
        if recorder.start_background_monitoring():
            # Keep running until interrupted
            while recorder.is_running:
                time.sleep(1)
        else:
            logger.error("Failed to start background monitoring")
            sys.exit(1)
            
    except KeyboardInterrupt:
        signal_handler(None, None)
    except Exception as e:
        logger.error(f"Error: {e}")
        if 'recorder' in globals():
            recorder.stop_monitoring()
        sys.exit(1)


if __name__ == "__main__":
    main()
