#!/usr/bin/env python3
"""
Authentication middleware for Memex Prometheus Server.

Bearer token authentication with per-instance and master keys.
Keys are loaded from /ssd/memex/config/api_keys.env.
"""

import logging
import os
from pathlib import Path
from typing import Dict, Optional, Tuple

from fastapi import Request

logger = logging.getLogger(__name__)


class AuthManager:
    """Manages API key authentication for Memex instances."""

    def __init__(self, api_keys_path: str = "/ssd/memex/config/api_keys.env"):
        self.instance_keys: Dict[str, str] = {}
        self.master_key: Optional[str] = None
        self._load_keys(api_keys_path)

    def _load_keys(self, path: str):
        """Load API keys from env file."""
        keys_file = Path(path)
        if not keys_file.exists():
            logger.warning(f"API keys file not found: {path}")
            # Fall back to environment variables
            self._load_from_env()
            return

        with open(keys_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' not in line:
                    continue
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()

                if key == "MASTER_API_KEY":
                    self.master_key = value
                elif key.endswith("_API_KEY"):
                    # Extract instance name: PERSONAL_API_KEY -> personal
                    instance = key.replace("_API_KEY", "").lower()
                    self.instance_keys[instance] = value

        logger.info(f"Loaded API keys: {len(self.instance_keys)} instance keys, master={'yes' if self.master_key else 'no'}")

    def _load_from_env(self):
        """Fall back to environment variables."""
        self.master_key = os.environ.get("MASTER_API_KEY")
        for name in ["personal", "walmart", "alaska"]:
            key = os.environ.get(f"{name.upper()}_API_KEY")
            if key:
                self.instance_keys[name] = key

    def authenticate(self, request: Request, instance: str) -> Tuple[bool, str]:
        """
        Authenticate a request for a specific instance.

        Returns:
            (is_authenticated, error_message)
        """
        auth_header = request.headers.get("Authorization", "")

        if not auth_header:
            return False, "Missing Authorization header"

        if not auth_header.startswith("Bearer "):
            return False, "Invalid Authorization format. Use: Bearer <token>"

        token = auth_header[7:]  # Strip "Bearer "

        if not token:
            return False, "Empty bearer token"

        # Check master key
        if self.master_key and token == self.master_key:
            return True, ""

        # Check instance-specific key
        instance_key = self.instance_keys.get(instance)
        if instance_key and token == instance_key:
            return True, ""

        return False, "Invalid API key"
