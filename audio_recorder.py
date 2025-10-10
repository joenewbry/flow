#!/usr/bin/env python3
"""
Audio Recording and Transcription Script
Records system audio and transcribes it to text files for session history.
Perfect for capturing Zoom calls and other audio sessions.
"""

import os
import sys
import time
import threading
import queue
import signal
from datetime import datetime
from pathlib import Path
import json
import argparse

import pyaudio
import wave
import whisper
import numpy as np


class AudioRecorder:
    def __init__(self, output_dir="audio_sessions", model_size="base", chunk_duration=30):
        """
        Initialize the audio recorder.
        
        Args:
            output_dir: Directory to save audio and transcription files
            model_size: Whisper model size (tiny, base, small, medium, large)
            chunk_duration: Duration in seconds for each audio chunk to transcribe
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.chunk_duration = chunk_duration
        self.is_recording = False
        self.audio_queue = queue.Queue()
        
        # Audio settings
        self.sample_rate = 44100
        self.channels = 2
        self.chunk_size = 1024
        self.format = pyaudio.paInt16
        
        # Initialize PyAudio
        self.audio = pyaudio.PyAudio()
        
        # Load Whisper model
        print(f"Loading Whisper model ({model_size})...")
        self.whisper_model = whisper.load_model(model_size)
        print("Model loaded successfully!")
        
        # Session info
        self.session_start = None
        self.session_id = None
        self.audio_file = None
        self.transcript_file = None
        self.session_data = {
            "start_time": None,
            "end_time": None,
            "duration": None,
            "transcript": [],
            "audio_file": None
        }
    
    def get_default_input_device(self):
        """Get the default input device that can capture system audio."""
        try:
            # Try to find a device that can capture system audio
            default_device = self.audio.get_default_input_device_info()
            print(f"Using default input device: {default_device['name']}")
            return default_device['index']
        except Exception as e:
            print(f"Error getting default device: {e}")
            # List available devices
            print("\nAvailable audio devices:")
            for i in range(self.audio.get_device_count()):
                info = self.audio.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    print(f"  {i}: {info['name']} (channels: {info['maxInputChannels']})")
            return None
    
    def start_session(self, session_name=None):
        """Start a new recording session."""
        self.session_start = datetime.now()
        self.session_id = session_name or f"session_{self.session_start.strftime('%Y%m%d_%H%M%S')}"
        
        # Create session directory
        session_dir = self.output_dir / self.session_id
        session_dir.mkdir(exist_ok=True)
        
        # Set up file paths
        self.audio_file = session_dir / f"{self.session_id}.wav"
        self.transcript_file = session_dir / f"{self.session_id}_transcript.txt"
        self.json_file = session_dir / f"{self.session_id}_session.json"
        
        # Initialize session data
        self.session_data = {
            "session_id": self.session_id,
            "start_time": self.session_start.isoformat(),
            "end_time": None,
            "duration": None,
            "transcript": [],
            "audio_file": str(self.audio_file.name)
        }
        
        print(f"\n🎙️  Starting session: {self.session_id}")
        print(f"📁 Session directory: {session_dir}")
        print(f"🎵 Audio file: {self.audio_file.name}")
        print(f"📝 Transcript file: {self.transcript_file.name}")
        
        # Start recording
        self.is_recording = True
        
        # Start recording thread
        self.recording_thread = threading.Thread(target=self._record_audio)
        self.recording_thread.daemon = True
        self.recording_thread.start()
        
        # Start transcription thread
        self.transcription_thread = threading.Thread(target=self._transcribe_audio)
        self.transcription_thread.daemon = True
        self.transcription_thread.start()
        
        print("✅ Recording started! Press Ctrl+C to stop.")
    
    def _record_audio(self):
        """Record audio in a separate thread."""
        device_index = self.get_default_input_device()
        if device_index is None:
            print("❌ No suitable input device found!")
            return
        
        try:
            stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=self.chunk_size
            )
            
            frames = []
            chunk_frames = []
            chunk_start_time = time.time()
            
            print("🔴 Recording audio...")
            
            while self.is_recording:
                try:
                    data = stream.read(self.chunk_size, exception_on_overflow=False)
                    frames.append(data)
                    chunk_frames.append(data)
                    
                    # Check if we should process a chunk for transcription
                    if time.time() - chunk_start_time >= self.chunk_duration:
                        # Put chunk in queue for transcription
                        chunk_audio = b''.join(chunk_frames)
                        timestamp = datetime.now()
                        self.audio_queue.put((chunk_audio, timestamp))
                        
                        # Reset for next chunk
                        chunk_frames = []
                        chunk_start_time = time.time()
                        
                except Exception as e:
                    if self.is_recording:  # Only print error if we're still supposed to be recording
                        print(f"Error reading audio: {e}")
                    break
            
            # Process final chunk if any
            if chunk_frames:
                chunk_audio = b''.join(chunk_frames)
                timestamp = datetime.now()
                self.audio_queue.put((chunk_audio, timestamp))
            
            stream.stop_stream()
            stream.close()
            
            # Save complete audio file
            if frames:
                print("💾 Saving audio file...")
                wf = wave.open(str(self.audio_file), 'wb')
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.audio.get_sample_size(self.format))
                wf.setframerate(self.sample_rate)
                wf.writeframes(b''.join(frames))
                wf.close()
                print(f"✅ Audio saved to: {self.audio_file}")
            
        except Exception as e:
            print(f"❌ Recording error: {e}")
    
    def _transcribe_audio(self):
        """Transcribe audio chunks in a separate thread."""
        print("🤖 Transcription thread started...")
        
        while self.is_recording or not self.audio_queue.empty():
            try:
                # Get audio chunk from queue (with timeout)
                chunk_audio, timestamp = self.audio_queue.get(timeout=1.0)
                
                # Convert audio data to numpy array
                audio_np = np.frombuffer(chunk_audio, dtype=np.int16).astype(np.float32) / 32768.0
                
                # If stereo, convert to mono
                if self.channels == 2:
                    audio_np = audio_np.reshape(-1, 2).mean(axis=1)
                
                # Skip if audio is too quiet (likely silence)
                if np.max(np.abs(audio_np)) < 0.01:
                    continue
                
                print(f"🔍 Transcribing chunk from {timestamp.strftime('%H:%M:%S')}...")
                
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
                    self.session_data["transcript"].append(transcript_entry)
                    
                    # Write to transcript file
                    with open(self.transcript_file, 'a', encoding='utf-8') as f:
                        f.write(f"[{timestamp.strftime('%H:%M:%S')}] {text}\n")
                    
                    # Print to console
                    print(f"📝 [{timestamp.strftime('%H:%M:%S')}] {text}")
                    
                    # Save session data
                    self._save_session_data()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"❌ Transcription error: {e}")
                continue
    
    def _save_session_data(self):
        """Save session data to JSON file."""
        try:
            with open(self.json_file, 'w', encoding='utf-8') as f:
                json.dump(self.session_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving session data: {e}")
    
    def stop_session(self):
        """Stop the current recording session."""
        if not self.is_recording:
            return
        
        print("\n🛑 Stopping recording...")
        self.is_recording = False
        
        # Wait for threads to finish
        if hasattr(self, 'recording_thread'):
            self.recording_thread.join(timeout=5)
        if hasattr(self, 'transcription_thread'):
            self.transcription_thread.join(timeout=10)
        
        # Finalize session data
        session_end = datetime.now()
        duration = session_end - self.session_start
        
        self.session_data.update({
            "end_time": session_end.isoformat(),
            "duration": str(duration)
        })
        
        # Save final session data
        self._save_session_data()
        
        # Write session summary
        with open(self.transcript_file, 'a', encoding='utf-8') as f:
            f.write(f"\n--- Session Summary ---\n")
            f.write(f"Session ID: {self.session_id}\n")
            f.write(f"Start Time: {self.session_start.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"End Time: {session_end.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Duration: {duration}\n")
            f.write(f"Total Transcript Entries: {len(self.session_data['transcript'])}\n")
        
        print(f"✅ Session completed!")
        print(f"📊 Duration: {duration}")
        print(f"📝 Transcript entries: {len(self.session_data['transcript'])}")
        print(f"📁 Files saved in: {self.output_dir / self.session_id}")
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        if hasattr(self, 'audio'):
            self.audio.terminate()


def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully."""
    print("\n🛑 Received interrupt signal...")
    if 'recorder' in globals():
        recorder.stop_session()
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="Record and transcribe audio sessions")
    parser.add_argument("--output-dir", default="audio_sessions", 
                       help="Directory to save recordings (default: audio_sessions)")
    parser.add_argument("--model", default="base", 
                       choices=["tiny", "base", "small", "medium", "large"],
                       help="Whisper model size (default: base)")
    parser.add_argument("--chunk-duration", type=int, default=30,
                       help="Duration in seconds for transcription chunks (default: 30)")
    parser.add_argument("--session-name", 
                       help="Custom session name (default: auto-generated)")
    
    args = parser.parse_args()
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Create recorder
        global recorder
        recorder = AudioRecorder(
            output_dir=args.output_dir,
            model_size=args.model,
            chunk_duration=args.chunk_duration
        )
        
        # Start session
        recorder.start_session(args.session_name)
        
        # Keep running until interrupted
        while recorder.is_recording:
            time.sleep(1)
            
    except KeyboardInterrupt:
        signal_handler(None, None)
    except Exception as e:
        print(f"❌ Error: {e}")
        if 'recorder' in globals():
            recorder.stop_session()


if __name__ == "__main__":
    main()

