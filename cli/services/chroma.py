"""ChromaDB server service - start/stop the ChromaDB server."""

import shutil
import subprocess
from pathlib import Path
from typing import Optional, Tuple

from cli.config import get_settings


def get_chroma_command() -> Tuple[Optional[str], list[str]]:
    """
    Get the command to run ChromaDB server.
    Returns (description, cmd_list) or (None, []) if not found.
    Tries: venv chroma, python -m chromadb.cli.cli
    """
    settings = get_settings()

    # 1. venv chroma binary (install: ~/.memex/.venv, repo: refinery/.venv or mcp-server/.venv)
    for base in [
        settings.project_root / ".venv",
        settings.refinery_path / ".venv",
        settings.mcp_server_path / ".venv",
    ]:
        chroma_bin = base / "bin" / "chroma"
        if chroma_bin.exists():
            return str(chroma_bin), [str(chroma_bin), "run", "--host", settings.chroma_host, "--port", str(settings.chroma_port)]

    # 2. venv python -m chromadb.cli.cli (chromadb provides this)
    for base in [
        settings.project_root / ".venv",
        settings.refinery_path / ".venv",
        settings.mcp_server_path / ".venv",
    ]:
        py = base / "bin" / "python"
        if py.exists():
            return str(py), [
                str(py), "-m", "chromadb.cli.cli", "run",
                "--host", settings.chroma_host, "--port", str(settings.chroma_port),
            ]

    # 3. system chroma or python
    chroma = shutil.which("chroma")
    if chroma:
        return chroma, [chroma, "run", "--host", settings.chroma_host, "--port", str(settings.chroma_port)]

    return None, []
