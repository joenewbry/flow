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

- [x] Remove audio recording Python files
  - [x] Delete `audio_recorder.py`
  - [x] Delete `audio_background_recorder.py`

- [x] Remove audio-related shell scripts
  - [x] Delete `setup_audio_recorder.sh`
  - [x] Delete `start_audio_background.sh`

- [x] Remove audio-related requirements file
  - [x] Delete `audio_requirements.txt`

- [x] Remove audio-related directories
  - [x] Delete `audio_env/` virtual environment directory
  - [x] Delete `audio_sessions/` directory (if exists)
  - [x] Delete `refinery/data/audio/` directory (if exists)

- [x] Remove audio-related markdown documentation files
  - [x] Delete `AUDIO_BACKGROUND_README.md`
  - [x] Delete `AUDIO_RECORDER_README.md`
  - [x] Delete `AUDIO_SETUP_COMPLETE.md`
  - [x] Delete `AUDIO_SETUP_GUIDE.md`
  - [x] Delete `AUDIO_DUAL_CAPTURE_SUMMARY.md`
  - [x] Delete `AUDIO_SEARCH_FIX.md`

- [x] Remove audio references from code files
  - [x] Remove audio-related code from `mcp-server/tools/search.py` (audio file reading, audio search logic)
  - [x] Check and remove audio references from `mcp-server/server.py`
  - [x] Update comments in `refinery/run.py` (remove "Tag to differentiate from audio" comments)
  - [x] Update comments in `refinery/load_ocr_data.py` (remove "Tag to differentiate from audio" comments)

- [x] Remove audio references from README.md
  - [x] Remove audio recording setup section
  - [x] Remove audio transcription pipeline description
  - [x] Remove audio data type references from search capabilities
  - [x] Remove audio-related environment variables
  - [x] Remove audio-related architecture diagrams and descriptions

- [x] Remove audio-related pip packages from requirements files
  - [x] Check `refinery/flow-requirements.txt` for audio packages (pyaudio, whisper, openai if only used for audio)
  - [x] Check `mcp-server/requirements.txt` for audio packages
  - [x] Remove any audio-specific dependencies

- [x] Remove audio log files
  - [x] Delete `audio_background.log` (if exists)

- [x] Remove non-core directories and folders
  - [x] Delete `dashboard/` directory (web dashboard not needed for core OCR/ChromaDB/NGROK)
  - [x] Delete `images/` directory (images not needed for core functionality)
  - [x] Delete `website-builder/` directory (website builder not needed for core functionality)
  - [x] Delete `refinery/data/test_images/` directory (test data not needed)
  - [x] Delete `refinery/test_screenshot.py` (test file not needed for production)
  - [x] Delete `refinery/countdown_broadcaster.py` (dashboard-related, not needed for core functionality)

- [x] Remove website-builder related code from MCP server
  - [x] Check `mcp-server/tools/website.py` - remove or update if website builder functionality is not core
  - [x] Check `mcp-server/http_server.py` - remove website-builder references if not needed for NGROK MCP server

- [x] Move all markdown files to workspace folder
  - [x] Create `workspace/` directory if it doesn't exist
  - [x] Move all `.md` files from root directory to `workspace/` (except README.md and cleanup.md)
  - [x] Update any references to moved markdown files in code or documentation

- [x] Create simplified README (200 lines or fewer)
  - [x] Create new simplified README focusing only on OCR capture, ChromaDB storage, and NGROK availability
  - [x] Include quick start instructions
  - [x] Include Claude Desktop integration steps
  - [x] Include basic troubleshooting
  - [x] Keep installation instructions simple and clear for hacker news audience
  - [x] Remove all audio-related content
  - [x] Remove team collaboration features (if not directly related to core functionality)
  - [x] Remove dashboard references (if not core to OCR/ChromaDB/NGROK)
  - [x] Focus on essential setup and usage only
