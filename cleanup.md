# Cleanup

I'd like to make this codebase easier to maintain and use.


- Please make a todolist at the end of this file with steps to do in this format
- [ ] Item 1
- [ ] etc


The goal is to:

- remove all audio recording and processing code, including required pip packages
- remove any other code that isn't directly related to OCR capture, storage in chroma, and availability over NGROK

Please also make a TODO iteam for an example readme that is 200 or fewer lines. Want to make sure installation is easy for hacker news crowd

Also please move all of these .md files to a folder called workspace


## TODO List

- [ ] Remove audio recording Python files
  - [ ] Delete `audio_recorder.py`
  - [ ] Delete `audio_background_recorder.py`

- [ ] Remove audio-related shell scripts
  - [ ] Delete `setup_audio_recorder.sh`
  - [ ] Delete `start_audio_background.sh`

- [ ] Remove audio-related requirements file
  - [ ] Delete `audio_requirements.txt`

- [ ] Remove audio-related directories
  - [ ] Delete `audio_env/` virtual environment directory
  - [ ] Delete `audio_sessions/` directory (if exists)
  - [ ] Delete `refinery/data/audio/` directory (if exists)

- [ ] Remove audio-related markdown documentation files
  - [ ] Delete `AUDIO_BACKGROUND_README.md`
  - [ ] Delete `AUDIO_RECORDER_README.md`
  - [ ] Delete `AUDIO_SETUP_COMPLETE.md`
  - [ ] Delete `AUDIO_SETUP_GUIDE.md`
  - [ ] Delete `AUDIO_DUAL_CAPTURE_SUMMARY.md`
  - [ ] Delete `AUDIO_SEARCH_FIX.md`

- [ ] Remove audio references from code files
  - [ ] Remove audio-related code from `mcp-server/tools/search.py` (audio file reading, audio search logic)
  - [ ] Check and remove audio references from `mcp-server/server.py`
  - [ ] Update comments in `refinery/run.py` (remove "Tag to differentiate from audio" comments)
  - [ ] Update comments in `refinery/load_ocr_data.py` (remove "Tag to differentiate from audio" comments)

- [ ] Remove audio references from README.md
  - [ ] Remove audio recording setup section
  - [ ] Remove audio transcription pipeline description
  - [ ] Remove audio data type references from search capabilities
  - [ ] Remove audio-related environment variables
  - [ ] Remove audio-related architecture diagrams and descriptions

- [ ] Remove audio-related pip packages from requirements files
  - [ ] Check `refinery/flow-requirements.txt` for audio packages (pyaudio, whisper, openai if only used for audio)
  - [ ] Check `mcp-server/requirements.txt` for audio packages
  - [ ] Remove any audio-specific dependencies

- [ ] Remove audio log files
  - [ ] Delete `audio_background.log` (if exists)

- [ ] Remove non-core directories and folders
  - [ ] Delete `dashboard/` directory (web dashboard not needed for core OCR/ChromaDB/NGROK)
  - [ ] Delete `images/` directory (images not needed for core functionality)
  - [ ] Delete `website-builder/` directory (website builder not needed for core functionality)
  - [ ] Delete `refinery/data/test_images/` directory (test data not needed)
  - [ ] Delete `refinery/test_screenshot.py` (test file not needed for production)
  - [ ] Delete `refinery/countdown_broadcaster.py` (dashboard-related, not needed for core functionality)

- [ ] Remove website-builder related code from MCP server
  - [ ] Check `mcp-server/tools/website.py` - remove or update if website builder functionality is not core
  - [ ] Check `mcp-server/http_server.py` - remove website-builder references if not needed for NGROK MCP server

- [ ] Move all markdown files to workspace folder
  - [ ] Create `workspace/` directory if it doesn't exist
  - [ ] Move all `.md` files from root directory to `workspace/` (except README.md and cleanup.md)
  - [ ] Update any references to moved markdown files in code or documentation

- [ ] Create simplified README (200 lines or fewer)
  - [ ] Create new simplified README focusing only on OCR capture, ChromaDB storage, and NGROK availability
  - [ ] Include quick start instructions
  - [ ] Include Claude Desktop integration steps
  - [ ] Include basic troubleshooting
  - [ ] Keep installation instructions simple and clear for hacker news audience
  - [ ] Remove all audio-related content
  - [ ] Remove team collaboration features (if not directly related to core functionality)
  - [ ] Remove dashboard references (if not core to OCR/ChromaDB/NGROK)
  - [ ] Focus on essential setup and usage only
