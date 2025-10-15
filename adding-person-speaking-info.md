# Technical Plan: Adding Speaker Identification (Speaker Diarization)

## Overview

This document outlines how to add speaker identification to the audio transcription system, allowing the system to identify **who said what** in audio recordings (meetings, calls, etc.).

## Current State

**What We Have:**
- ✅ Audio capture (microphone + system audio)
- ✅ Transcription via OpenAI Whisper API
- ✅ Timestamped transcripts saved as markdown
- ✅ ChromaDB integration with searchable transcripts

**What We're Missing:**
- ❌ Speaker identification ("Speaker 1", "Speaker 2", etc.)
- ❌ Speaker labeling (associating speakers with names)
- ❌ Per-speaker transcript segments

## Goal

Add speaker diarization to produce transcripts like:

```markdown
# Audio Transcript: auto_20241015_143022

**Session Start:** 2024-10-15T14:30:22

---

## [14:30:25] Speaker 1 (Joe)

Welcome everyone to today's standup meeting.

## [14:30:42] Speaker 2 (Sarah)

Thanks! I worked on the authentication system yesterday.

## [14:31:15] Speaker 1 (Joe)

Great work! Let me share my screen and show you what I built...
```

## OpenAI Whisper API Capabilities

### ❌ What OpenAI Whisper API Does NOT Provide

Unfortunately, **OpenAI's Whisper API does not include speaker diarization**. The `whisper-1` model only provides:
- ✅ Transcription (speech-to-text)
- ✅ Language detection
- ✅ Timestamps (for segments)
- ❌ **Speaker identification** (not available)

### Why Not?

OpenAI's hosted Whisper API is focused on transcription only. Speaker diarization is a separate, more complex task that requires:
- Voice profile analysis
- Speaker clustering/separation
- Temporal speaker assignment

## Solution Options

### Option 1: AssemblyAI API (Recommended) ⭐

**Best balance of ease and quality.**

#### Pros:
- ✅ Built-in speaker diarization
- ✅ Automatic speaker labeling (Speaker A, Speaker B, etc.)
- ✅ High accuracy
- ✅ Simple API
- ✅ Timestamps per speaker segment
- ✅ Can specify number of speakers

#### Cons:
- 💰 Additional cost (~$0.015/minute for transcription + diarization)
- 🔄 Requires switching from OpenAI to AssemblyAI

#### Implementation:

```python
import assemblyai as aai

# Configure
aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")

# Transcribe with diarization
config = aai.TranscriptionConfig(
    speaker_labels=True,
    speakers_expected=2  # Optional: hint for number of speakers
)

transcriber = aai.Transcriber()
transcript = transcriber.transcribe(audio_file, config=config)

# Get speaker-segmented results
for utterance in transcript.utterances:
    print(f"Speaker {utterance.speaker}: {utterance.text}")
    # Speaker A: Welcome everyone
    # Speaker B: Thanks for having me
```

#### Cost:
- Base transcription: $0.010/minute
- Speaker diarization: +$0.005/minute
- **Total: ~$0.015/minute** (vs OpenAI's $0.006/minute)
- **1-hour meeting: ~$0.90** (very reasonable)

---

### Option 2: Deepgram API (Alternative)

**Another commercial option with good quality.**

#### Pros:
- ✅ Built-in diarization
- ✅ Fast real-time transcription
- ✅ Good accuracy
- ✅ Competitive pricing

#### Cons:
- 💰 Similar pricing to AssemblyAI
- 🔄 Requires API switch

#### Cost:
- Pay-as-you-go: $0.0125/minute with diarization
- **1-hour meeting: ~$0.75**

---

### Option 3: Pyannote.audio (Open Source) 🆓

**Free but requires more work.**

#### Pros:
- ✅ Free and open source
- ✅ Good accuracy
- ✅ Runs locally (privacy)
- ✅ Can use with existing OpenAI Whisper API

#### Cons:
- ⚙️ More complex setup
- 🐌 Slower (runs locally)
- 💻 Requires GPU for good performance
- 🔧 Two-step process (transcribe + diarize)

#### Implementation:

```python
from pyannote.audio import Pipeline
import torch

# Load speaker diarization pipeline
pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-3.1",
    use_auth_token="YOUR_HUGGINGFACE_TOKEN"
)

# Run diarization
diarization = pipeline(audio_file)

# Get speaker segments
for turn, _, speaker in diarization.itertracks(yield_label=True):
    print(f"{turn.start:.1f}s - {turn.end:.1f}s: {speaker}")
    # 0.5s - 3.2s: SPEAKER_00
    # 3.2s - 8.1s: SPEAKER_01

# Then combine with OpenAI Whisper transcription
```

#### Requirements:
- HuggingFace account (free)
- Additional Python packages
- GPU recommended (but can run on CPU)

---

### Option 4: OpenAI Whisper Local + Pyannote (Hybrid)

**Use local Whisper model with pyannote for full control.**

#### Pros:
- ✅ Free (no API costs)
- ✅ Complete privacy (all local)
- ✅ Full control

#### Cons:
- 💻 High CPU/GPU requirements
- 🐌 Much slower
- 💾 Large model downloads
- ⚙️ Complex setup

Not recommended unless you have strong privacy requirements.

---

## Recommended Approach: AssemblyAI

### Why AssemblyAI?

1. **Easiest Integration**: Drop-in replacement for OpenAI API
2. **Best Quality**: State-of-the-art diarization
3. **Reasonable Cost**: Only ~$0.009/minute more than OpenAI
4. **Proven**: Used by many production apps
5. **Features**: Automatic punctuation, speaker labels, timestamps

### Implementation Plan

#### Phase 1: Basic Integration (2-3 hours)

1. **Add AssemblyAI to requirements:**
   ```bash
   echo "assemblyai>=0.20.0" >> audio_requirements.txt
   ```

2. **Update `audio_background_recorder.py`:**
   - Add AssemblyAI client initialization
   - Modify `_transcribe_audio()` to use AssemblyAI
   - Parse speaker information from response
   - Update markdown format to include speakers

3. **Update `.env` file:**
   ```bash
   ASSEMBLYAI_API_KEY=your-key-here
   ```

4. **Modify markdown output:**
   ```python
   # Instead of:
   f.write(f"## [{timestamp}]\n\n{text}\n\n")
   
   # Write:
   f.write(f"## [{timestamp}] Speaker {speaker_label}\n\n{text}\n\n")
   ```

5. **Update ChromaDB metadata:**
   ```python
   metadata = {
       "timestamp": timestamp,
       "data_type": "audio",
       "speaker": speaker_label,  # NEW
       "text": text,
       ...
   }
   ```

#### Phase 2: Speaker Naming (Additional 1-2 hours)

Add ability to label speakers with actual names:

1. **Create speaker mapping config:**
   ```json
   {
     "speakers": {
       "SPEAKER_00": "Joe",
       "SPEAKER_01": "Sarah",
       "SPEAKER_02": "Mike"
     }
   }
   ```

2. **Add CLI command to update speaker names:**
   ```bash
   python audio_background_recorder.py --name-speaker SPEAKER_00 "Joe"
   ```

3. **Apply names in real-time or post-process**

#### Phase 3: Voice Profiles (Future Enhancement)

- Save voice fingerprints for known speakers
- Automatically identify speakers across sessions
- "That sounds like Joe" recognition

### Code Changes Required

**File: `audio_background_recorder.py`**

```python
# Add at top
import assemblyai as aai

# In __init__():
# Initialize AssemblyAI
assemblyai_key = os.getenv("ASSEMBLYAI_API_KEY")
if assemblyai_key:
    aai.settings.api_key = assemblyai_key
    self.use_assemblyai = True
    logger.info("Using AssemblyAI for transcription with speaker diarization")
else:
    self.use_assemblyai = False
    logger.info("Using OpenAI Whisper (no speaker diarization)")

# In _transcribe_audio():
if self.use_assemblyai:
    # Upload audio to AssemblyAI
    config = aai.TranscriptionConfig(speaker_labels=True)
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(temp_path, config=config)
    
    # Process speaker-segmented utterances
    for utterance in transcript.utterances:
        transcript_entry = {
            "timestamp": timestamp.isoformat(),
            "text": utterance.text,
            "speaker": utterance.speaker,  # e.g., "A", "B", "C"
            "start": utterance.start,
            "end": utterance.end
        }
        
        # Append to markdown with speaker label
        with open(session['markdown_file'], 'a', encoding='utf-8') as f:
            f.write(f"## [{format_time(utterance.start)}] Speaker {utterance.speaker}\n\n")
            f.write(f"{utterance.text}\n\n")
else:
    # Existing OpenAI code (no speakers)
    ...
```

### Migration Path

**Option A: Immediate Switch**
- Update code to use AssemblyAI for all new recordings
- Old recordings keep OpenAI format (no speakers)

**Option B: Dual Mode**
- Keep both APIs available
- Let user choose via config or command-line flag
- Default to AssemblyAI if key present, else OpenAI

**Option C: Gradual (Recommended)**
1. Add AssemblyAI support alongside OpenAI
2. Test with a few recordings
3. Compare quality and cost
4. Switch default after validation

### Testing Plan

1. **Record test audio** with 2-3 speakers
2. **Verify speaker separation** is accurate
3. **Check markdown formatting** looks good
4. **Test ChromaDB search** with speaker filter
5. **Validate cost** matches expectations

### Cost Comparison

**OpenAI Whisper:**
- $0.006/minute
- 1-hour meeting = $0.36
- ❌ No speakers

**AssemblyAI:**
- $0.015/minute (with diarization)
- 1-hour meeting = $0.90
- ✅ Speaker labels

**Cost Increase:** +$0.54 per hour
**Worth it?** YES - knowing who said what is valuable

### Advanced Features (Future)

Once basic diarization works:

1. **Speaker Recognition**
   - Train on known voices
   - Auto-label familiar speakers
   - "Joe speaking" vs "Unknown Speaker 1"

2. **Voice Profiles**
   - Store voice embeddings
   - Match across sessions
   - Build speaker database

3. **Speaker Stats**
   - Who talked most?
   - Speaking time per person
   - Participation metrics

4. **Smart Search**
   - "What did Sarah say about the API?"
   - Filter by speaker in MCP tools
   - Speaker-specific summaries

## Recommended Next Steps

1. **✅ Sign up for AssemblyAI** (free tier available)
   - Get API key from https://www.assemblyai.com/

2. **✅ Update requirements.txt**
   ```bash
   pip install assemblyai
   ```

3. **✅ Add to `.env`:**
   ```
   ASSEMBLYAI_API_KEY=your-key-here
   ```

4. **✅ Implement basic integration** (2-3 hours)
   - Modify `_transcribe_audio()` method
   - Update markdown formatting
   - Test with sample audio

5. **✅ Test and validate** (1 hour)
   - Record test conversation
   - Verify speaker separation
   - Check accuracy

6. **✅ Deploy** and monitor costs

## Alternative: Start with Free Pyannote

If you want to try before paying:

1. Use pyannote.audio (free) for testing
2. Validate the feature is useful
3. Switch to AssemblyAI for production quality

## Summary

**Recommendation:** Use **AssemblyAI** for speaker diarization.

**Why:**
- ✅ Easiest to implement (~3 hours work)
- ✅ Best quality results
- ✅ Reasonable cost (+$0.009/min)
- ✅ Production-ready
- ✅ Minimal code changes

**Next Action:** 
Get AssemblyAI API key and implement Phase 1 (basic integration).

---

**Questions? Issues?**
- AssemblyAI docs: https://www.assemblyai.com/docs
- Pyannote docs: https://github.com/pyannote/pyannote-audio
- Deepgram docs: https://developers.deepgram.com/

