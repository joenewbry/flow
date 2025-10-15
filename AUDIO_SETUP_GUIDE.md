# 🎙️ Complete Audio Capture Setup Guide

This guide will help you set up Flow to capture **ALL audio**:
- 🎤 **Your microphone** (what you say)
- 🔊 **System audio** (YouTube, Zoom, music, all computer sounds)

## Why You Need BlackHole

macOS doesn't allow apps to directly capture system audio (for security reasons). To capture both microphone and system audio, you need:

1. **BlackHole**: A virtual audio driver that routes system audio
2. **Multi-Output Device**: Combines microphone + system audio
3. **ffmpeg**: Captures the combined audio stream

## Step-by-Step Setup

### Part 1: Install BlackHole

```bash
# Install BlackHole 2ch (2-channel audio device)
brew install blackhole-2ch
```

**What is BlackHole?**
- A free, open-source virtual audio driver
- Routes audio between applications
- Required for capturing system audio on macOS
- GitHub: https://github.com/ExistentialAudio/BlackHole

### Part 2: Configure Audio Routing

#### 2.1 Open Audio MIDI Setup

1. Press `Cmd + Space` and search for "Audio MIDI Setup"
2. Or go to: `/Applications/Utilities/Audio MIDI Setup.app`

#### 2.2 Create Multi-Output Device

1. Click the **"+"** button in bottom-left corner
2. Select **"Create Multi-Output Device"**
3. Check these devices:
   - ✅ **Your speakers/headphones** (e.g., "MacBook Pro Speakers" or your headphones)
   - ✅ **BlackHole 2ch**
4. **Important**: Make sure your speakers are listed **first** (so you can still hear audio)
5. Rename it to something memorable like "Main + BlackHole"

#### 2.3 Create Aggregate Device (for microphone + system audio)

1. Click the **"+"** button again
2. Select **"Create Aggregate Device"**
3. Check these devices:
   - ✅ **Built-in Microphone** (or your external microphone)
   - ✅ **BlackHole 2ch**
4. Rename it to "Mic + System Audio"

### Part 3: Set System Output

1. **System Settings** > **Sound** > **Output**
2. Select your **"Main + BlackHole"** multi-output device
3. This routes all system audio to both your speakers AND BlackHole

**Result**: You'll hear everything normally, but audio is also routed to BlackHole for recording.

### Part 4: Test the Setup

```bash
# Start the audio recorder
./start_audio_background.sh
```

You should see:
```
BlackHole detected - will attempt to capture both mic and system audio
Started ffmpeg audio capture (microphone + system audio if available)
✅ Background audio monitoring started!
```

### Part 5: Test with Real Audio

1. **Play a YouTube video** - it should be captured
2. **Talk into your microphone** - it should be captured
3. **Join a Zoom call** - both you and others should be captured
4. **Play music** - it should be captured

Check the output in `refinery/data/audio/*.md` to see transcripts!

## Audio Routing Diagram

```
┌─────────────────────────────────────────────────────────┐
│                      YOUR MAC                            │
│                                                          │
│  ┌──────────────┐                                       │
│  │ Microphone   │────┐                                  │
│  └──────────────┘    │                                  │
│                      ├──> Aggregate Device ──┐          │
│  ┌──────────────┐    │                       │          │
│  │ System Audio │────┤                       │          │
│  │ (YouTube,    │    │                       v          │
│  │  Zoom, etc.) │    └──> Multi-Output ───> BlackHole   │
│  └──────────────┘              │                │       │
│                                v                │       │
│                         Your Speakers           │       │
│                         (you hear it)           │       │
│                                                 │       │
│                                                 v       │
│                                              ffmpeg     │
│                                                 │       │
│                                                 v       │
│                                         Audio Recorder  │
│                                                 │       │
│                                                 v       │
│                                      Transcription      │
│                                      (OpenAI API)       │
│                                                 │       │
│                                                 v       │
│                                   refinery/data/audio/  │
│                                         *.md files      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Troubleshooting

### "BlackHole not detected"

**Problem**: The system only captures microphone
**Solution**:
1. Verify BlackHole is installed: `brew list | grep blackhole`
2. Make sure you set system output to the Multi-Output device
3. Restart the audio recorder

### "No audio captured"

**Problem**: No transcripts are being created
**Solutions**:
1. Check audio permissions in System Settings > Privacy & Security
2. Make sure ChromaDB is running
3. Check logs: `tail -f audio_background.log`
4. Test with: `ffmpeg -f avfoundation -list_devices true -i ""`

### "Can't hear audio anymore"

**Problem**: After setup, your speakers don't work
**Solution**:
1. Go to System Settings > Sound
2. Change output back to your speakers temporarily
3. To use Flow, switch back to "Main + BlackHole"

**Tip**: Create a keyboard shortcut or use an app like **BackgroundMusic** to quickly switch audio outputs.

### "Only capturing microphone"

**Problem**: Microphone works but no system audio (YouTube, etc.)
**Solution**:
1. Verify system output is set to Multi-Output device (not just speakers)
2. In Audio MIDI Setup, ensure BlackHole 2ch is checked in your Multi-Output
3. Restart the audio recording service

## What Gets Captured

With this setup, you'll capture:

✅ **Your voice** through the microphone  
✅ **Zoom/Teams calls** (both you and other participants)  
✅ **YouTube videos** and their audio  
✅ **Music** playing on your computer  
✅ **System notifications** and sounds  
✅ **Any application audio** (Slack calls, Discord, etc.)  

## Quick Setup Commands

```bash
# 1. Install BlackHole
brew install blackhole-2ch

# 2. Configure Audio MIDI Setup (manual steps above)

# 3. Set system output to Multi-Output device

# 4. Start audio recording
./start_audio_background.sh

# 5. Test by playing a YouTube video and talking
```

## Advanced: Automated Audio Switching

You can use AppleScript to automatically switch audio output:

```applescript
# Switch to Multi-Output (for recording)
osascript -e 'tell application "System Events" to tell process "SystemUIServer"
    set volume output volume 50
end tell'

# This can be automated with a script
```

Or use tools like:
- **BackgroundMusic** (free): Switch audio outputs with hotkeys
- **SwitchAudioSource** (CLI): `brew install switchaudio-osx`

## Testing Your Setup

Run this test to verify everything works:

```bash
# 1. Start audio recording
./start_audio_background.sh

# 2. Play this test:
say "Testing microphone capture"
open "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Play some audio

# 3. Wait 30 seconds, then check:
ls -lah refinery/data/audio/*.md
cat refinery/data/audio/*.md  # See the transcript
```

You should see transcripts of both the spoken text AND the YouTube audio!

## Important Notes

1. **Privacy**: You're recording ALL audio on your computer
2. **Legal**: Make sure you have permission to record calls/meetings
3. **Storage**: Audio files can be large - monitor disk space
4. **CPU**: Transcription uses OpenAI API (minimal CPU impact)
5. **Cost**: ~$0.006 per minute of audio transcription

## Uninstalling

To remove BlackHole:
```bash
brew uninstall blackhole-2ch
```

Then delete the Multi-Output and Aggregate devices in Audio MIDI Setup.

---

**Need Help?** Check the logs: `tail -f audio_background.log`


