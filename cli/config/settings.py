"""Settings and configuration for Memex CLI."""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

# Determine the project root (where this repo is located)
CLI_DIR = Path(__file__).parent.parent
PROJECT_ROOT = CLI_DIR.parent


@dataclass
class Settings:
    """Memex CLI settings."""

    # Paths
    project_root: Path = field(default_factory=lambda: PROJECT_ROOT)
    refinery_path: Path = field(default_factory=lambda: PROJECT_ROOT / "refinery")
    mcp_server_path: Path = field(default_factory=lambda: PROJECT_ROOT / "mcp-server")
    ocr_data_path: Path = field(default_factory=lambda: PROJECT_ROOT / "refinery" / "data" / "ocr")
    chroma_path: Path = field(default_factory=lambda: PROJECT_ROOT / "refinery" / "chroma")

    # ChromaDB settings
    chroma_host: str = "localhost"
    chroma_port: int = 8000
    chroma_collection: str = "screen_ocr_history"

    # Capture settings
    capture_interval: int = 60  # seconds

    # Config file location
    config_dir: Path = field(default_factory=lambda: Path.home() / ".memex")

    def __post_init__(self):
        """Ensure paths are Path objects."""
        if isinstance(self.project_root, str):
            self.project_root = Path(self.project_root)
        if isinstance(self.refinery_path, str):
            self.refinery_path = Path(self.refinery_path)
        if isinstance(self.mcp_server_path, str):
            self.mcp_server_path = Path(self.mcp_server_path)
        if isinstance(self.ocr_data_path, str):
            self.ocr_data_path = Path(self.ocr_data_path)
        if isinstance(self.chroma_path, str):
            self.chroma_path = Path(self.chroma_path)
        if isinstance(self.config_dir, str):
            self.config_dir = Path(self.config_dir)


# Singleton settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
