"""Instance configuration management for Memex CLI.

Manages hosting mode (local, jetson, remote) and instance connection details.
Stored at ~/.memex/instance.json with restricted permissions.
"""

import os
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, Literal

from cli.config.settings import get_settings

HostingMode = Literal["local", "jetson", "remote"]

DEFAULT_HOSTING_MODE: HostingMode = "jetson"
DEFAULT_INSTANCE_NAME = "personal"


@dataclass
class InstanceConfig:
    """Configuration for a Memex instance."""

    # Core
    hosting_mode: HostingMode = DEFAULT_HOSTING_MODE
    instance_name: str = DEFAULT_INSTANCE_NAME

    # Local mode (defaults from settings — no overrides needed)
    local_chroma_host: str = "localhost"
    local_chroma_port: int = 8000
    local_mcp_port: int = 8082

    # Jetson mode
    jetson_host: str = ""
    jetson_chroma_port: int = 8000
    jetson_mcp_port: int = 8082
    jetson_tunnel_url: str = ""

    # Remote self-host mode
    remote_host: str = ""
    remote_ssh_port: int = 22
    remote_chroma_port: int = 8000
    remote_mcp_port: int = 8082
    remote_tunnel_url: str = ""

    def get_chroma_host(self) -> str:
        """Return the ChromaDB host for the active hosting mode."""
        if self.hosting_mode == "jetson":
            return self.jetson_host or "localhost"
        elif self.hosting_mode == "remote":
            return self.remote_host or "localhost"
        return self.local_chroma_host

    def get_chroma_port(self) -> int:
        """Return the ChromaDB port for the active hosting mode."""
        if self.hosting_mode == "jetson":
            return self.jetson_chroma_port
        elif self.hosting_mode == "remote":
            return self.remote_chroma_port
        return self.local_chroma_port

    def get_mcp_port(self) -> int:
        """Return the MCP HTTP port for the active hosting mode."""
        if self.hosting_mode == "jetson":
            return self.jetson_mcp_port
        elif self.hosting_mode == "remote":
            return self.remote_mcp_port
        return self.local_mcp_port

    def get_tunnel_url(self) -> str:
        """Return the tunnel URL if configured for the active mode."""
        if self.hosting_mode == "jetson":
            return self.jetson_tunnel_url
        elif self.hosting_mode == "remote":
            return self.remote_tunnel_url
        return ""


def _get_instance_path() -> Path:
    """Get path to instance config file."""
    settings = get_settings()
    return settings.config_dir / "instance.json"


def _ensure_config_dir():
    """Ensure config directory exists with proper permissions."""
    settings = get_settings()
    settings.config_dir.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(settings.config_dir, 0o700)
    except Exception:
        pass


class InstanceService:
    """Manages instance configuration persistence."""

    def __init__(self):
        self._path = _get_instance_path()

    def exists(self) -> bool:
        """Check if an instance config file exists."""
        return self._path.exists()

    def load(self) -> InstanceConfig:
        """Load instance config from disk, or return defaults."""
        if not self._path.exists():
            return InstanceConfig()

        try:
            with open(self._path, "r") as f:
                data = json.load(f)
            # Only pass known fields to avoid errors on old/extra keys
            known_fields = {f.name for f in InstanceConfig.__dataclass_fields__.values()}
            filtered = {k: v for k, v in data.items() if k in known_fields}
            return InstanceConfig(**filtered)
        except Exception:
            return InstanceConfig()

    def save(self, config: InstanceConfig):
        """Save instance config to disk with restricted permissions."""
        _ensure_config_dir()
        with open(self._path, "w") as f:
            json.dump(asdict(config), f, indent=2)
        try:
            os.chmod(self._path, 0o600)
        except Exception:
            pass

    def set_hosting_mode(self, mode: HostingMode) -> InstanceConfig:
        """Switch hosting mode and persist."""
        config = self.load()
        config.hosting_mode = mode
        self.save(config)
        return config
