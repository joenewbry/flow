#!/usr/bin/env python3
"""
Background Audio Recording and Transcription Service
Automatically detects and records system audio (like Zoom calls) and stores transcripts in ChromaDB.
Designed to run as a background service alongside the Flow system.
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

import numpy as np
import whisper
import chromadb
from chromadb.errors import ChromaError

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
                 output_dir="audio_sessions", 
                 model_size="base", 
                 chunk_duration=30,
                 silence_threshold=0.01,
                 min_recording_duration=10,
                 chroma_host="localhost",
                 chroma_port=8000):
        """
        Initialize the background audio recorder.
        
        Args:
            output_dir: Directory to save audio and transcription files
            model_size: Whisper model size (tiny, base, small, medium, large)
            chunk_duration: Duration in seconds for each audio chunk to transcribe
            silence_threshold: Audio level below which is considered silence
            min_recording_duration: Minimum duration to keep a recording
            chroma_host: ChromaDB host
            chroma_port: ChromaDB port
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
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
        
        # Load Whisper model
        logger.info(f"Loading Whisper model ({model_size})...")
        self.whisper_model = whisper.load_model(model_size)
        logger.info("Whisper model loaded successfully!")
        
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
            
            # Get or create audio collection
            self.audio_collection = self.chroma_client.get_or_create_collection(
                name="audio_transcripts",
                metadata={"description": "Audio transcription data from background recording"}
            )
            logger.info("Audio collection initialized in ChromaDB")
            
        except Exception as e:
            logger.warning(f"ChromaDB connection failed: {e}")
            logger.warning("Audio will be saved locally but not stored in ChromaDB")
            self.chroma_client = None
    
    def detect_system_audio_method(self):
        """Detect the best method to capture system audio on macOS."""
        try:
            # Check if BlackHole is installed (recommended virtual audio driver)
            result = subprocess.run(['system_profiler', 'SPAudioDataType'], 
                                  capture_output=True, text=True)
            if 'BlackHole' in result.stdout:
                logger.info("BlackHole virtual audio driver detected")
                return "blackhole"
            
            # Check if SoundFlower is available
            if 'Soundflower' in result.stdout:
                logger.info("Soundflower virtual audio driver detected")
                return "soundflower"
            
            # Fall back to using ffmpeg with screen capture audio
            if subprocess.run(['which', 'ffmpeg'], capture_output=True).returncode == 0:
                logger.info("Using ffmpeg for system audio capture")
                return "ffmpeg"
            
            logger.warning("No suitable system audio capture method found")
            return None
            
        except Exception as e:
            logger.error(f"Error detecting audio method: {e}")
            return None
    
    def start_system_audio_capture(self):
        """Start capturing system audio using the best available method."""
        method = self.detect_system_audio_method()
        
        if method == "ffmpeg":
            return self._start_ffmpeg_capture()
        elif method in ["blackhole", "soundflower"]:
            return self._start_virtual_driver_capture(method)
        else:
            logger.error("No system audio capture method available")
            logger.info("Please install BlackHole (https://github.com/ExistentialAudio/BlackHole) for system audio capture")
            return None
    
    def _start_ffmpeg_capture(self):
        """Start audio capture using ffmpeg."""
        try:
            # Use ffmpeg to capture system audio
            cmd = [
                'ffmpeg',
                '-f', 'avfoundation',
                '-i', ':0',  # System audio
                '-ar', '44100',
                '-ac', '1',  # Mono
                '-f', 'wav',
                '-'  # Output to stdout
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0
            )
            
            logger.info("Started ffmpeg system audio capture")
            return process
            
        except Exception as e:
            logger.error(f"Failed to start ffmpeg capture: {e}")
            return None
    
    def _start_virtual_driver_capture(self, driver_name):
        """Start audio capture using virtual audio driver."""
        # This would require pyaudio setup with the virtual driver
        # For now, fall back to ffmpeg
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
        
        # Create session directory
        session_dir = self.output_dir / session_id
        session_dir.mkdir(exist_ok=True)
        
        self.current_session = {
            "session_id": session_id,
            "start_time": self.recording_start_time.isoformat(),
            "session_dir": session_dir,
            "audio_file": session_dir / f"{session_id}.wav",
            "transcript_file": session_dir / f"{session_id}_transcript.txt",
            "json_file": session_dir / f"{session_id}_session.json",
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
        """Transcribe audio chunks in a separate thread."""
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
                
                # Transcribe with Whisper
                result = self.whisper_model.transcribe(audio_np, fp16=False)
                text = result["text"].strip()
                
                if text:
                    # Add to session data
                    transcript_entry = {
                        "timestamp": timestamp.isoformat(),
                        "text": text,
                        "confidence": result.get("confidence", 0.0)
                    }
                    session["transcript"].append(transcript_entry)
                    
                    # Write to transcript file
                    with open(session['transcript_file'], 'a', encoding='utf-8') as f:
                        f.write(f"[{timestamp.strftime('%H:%M:%S')}] {text}\n")
                    
                    # Store in ChromaDB
                    self._store_in_chroma(transcript_entry, session)
                    
                    logger.info(f"📝 [{timestamp.strftime('%H:%M:%S')}] {text}")
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Transcription error: {e}")
                continue
    
    def _store_in_chroma(self, transcript_entry: Dict[str, Any], session: Dict[str, Any]):
        """Store transcript in ChromaDB."""
        if not self.chroma_client:
            return
        
        try:
            # Prepare content for embedding
            content = f"Audio transcript: {transcript_entry['text']}"
            
            # Prepare metadata
            metadata = {
                "timestamp": transcript_entry["timestamp"],
                "session_id": session["session_id"],
                "confidence": transcript_entry["confidence"],
                "source": "background_audio_recording",
                "task_category": "audio_transcript",
                "text_length": len(transcript_entry['text']),
                "word_count": len(transcript_entry['text'].split())
            }
            
            # Store in ChromaDB
            doc_id = f"{session['session_id']}_{transcript_entry['timestamp']}"
            
            self.audio_collection.add(
                documents=[content],
                metadatas=[metadata],
                ids=[doc_id]
            )
            
            logger.debug(f"Stored in ChromaDB: {doc_id}")
            
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
    parser.add_argument("--output-dir", default="audio_sessions", 
                       help="Directory to save recordings (default: audio_sessions)")
    parser.add_argument("--model", default="base", 
                       choices=["tiny", "base", "small", "medium", "large"],
                       help="Whisper model size (default: base)")
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
            model_size=args.model,
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
