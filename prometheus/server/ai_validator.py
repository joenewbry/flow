#!/usr/bin/env python3
"""
AI Validator for Memex Prometheus Server.

Uses Ollama (llama3.2:1b) to gate MCP tool requests against a security policy.
- Loads policy from security-policy.md
- Sends tool name + arguments to the model
- Gets ALLOW/DENY response
- 10-second timeout, default DENY on timeout
- Caches identical requests for 60 seconds
- Skips validation for safe tools
"""

import hashlib
import json
import logging
import time
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Tools that bypass AI validation
SAFE_TOOLS = {
    "what-can-i-do", "get-stats", "ping",
    "activity-graph", "daily-summary", "time-range-summary",
}

# Tools that still get heuristic checks but skip Ollama AI validation.
# The heuristic checks catch wildcards, SQL injection, prompt injection, etc.
HEURISTIC_ONLY_TOOLS = {
    "search-screenshots", "sample-time-range",
    "vector-search-windowed", "search-recent-relevant",
}


class AIValidator:
    """Ollama-based request validator."""

    def __init__(self, ollama_host: str = "http://localhost:11434",
                 ollama_model: str = "llama3.2:1b",
                 policy_path: str = "/ssd/memex/config/security-policy.md",
                 timeout: float = 10.0, cache_ttl: int = 60):
        self.ollama_host = ollama_host
        self.ollama_model = ollama_model
        self.timeout = timeout
        self.cache_ttl = cache_ttl
        self.policy = self._load_policy(policy_path)
        self.cache: Dict[str, Tuple[bool, float]] = {}  # hash -> (allowed, timestamp)
        self.enabled = True

    def _load_policy(self, path: str) -> str:
        """Load security policy from file."""
        try:
            with open(path, 'r') as f:
                return f.read()
        except Exception as e:
            logger.warning(f"Could not load security policy from {path}: {e}")
            return "DENY all requests by default. No policy file found."

    def _cache_key(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Generate cache key for a request."""
        raw = f"{tool_name}:{json.dumps(arguments, sort_keys=True)}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def _check_cache(self, key: str) -> Optional[bool]:
        """Check if result is cached and not expired."""
        if key in self.cache:
            allowed, timestamp = self.cache[key]
            if time.time() - timestamp < self.cache_ttl:
                return allowed
            else:
                del self.cache[key]
        return None

    def _update_cache(self, key: str, allowed: bool):
        """Update cache with result."""
        self.cache[key] = (allowed, time.time())
        # Evict old entries if cache grows too large
        if len(self.cache) > 10000:
            cutoff = time.time() - self.cache_ttl
            self.cache = {k: v for k, v in self.cache.items() if v[1] > cutoff}

    async def validate(self, tool_name: str, arguments: Dict[str, Any],
                       instance: str = "") -> Tuple[bool, str]:
        """
        Validate a tool request against the security policy.

        Returns:
            (allowed, reason)
        """
        # Skip validation for safe tools
        if tool_name in SAFE_TOOLS:
            return True, "safe_tool"

        if not self.enabled:
            return True, "validation_disabled"

        # Check cache
        cache_key = self._cache_key(tool_name, arguments)
        cached = self._check_cache(cache_key)
        if cached is not None:
            return cached, "cached"

        # Quick heuristic checks before calling Ollama
        denied, reason = self._heuristic_check(tool_name, arguments)
        if denied:
            self._update_cache(cache_key, False)
            return False, reason

        # Heuristic-only tools pass if they survived the heuristic checks above
        if tool_name in HEURISTIC_ONLY_TOOLS:
            self._update_cache(cache_key, True)
            return True, "heuristic_passed"

        # Call Ollama for AI validation on remaining tools
        try:
            allowed, reason = await self._ollama_validate(tool_name, arguments, instance)
            self._update_cache(cache_key, allowed)
            return allowed, reason
        except Exception as e:
            logger.error(f"AI validation error: {e}")
            # Default DENY on error
            return False, f"validation_error: {e}"

    def _heuristic_check(self, tool_name: str, arguments: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Quick heuristic checks before calling Ollama.
        Returns (should_deny, reason). If should_deny is False, proceed to Ollama.
        """
        query = arguments.get("query", "")

        # Check for wildcard/empty queries
        if tool_name in ("search-screenshots", "vector-search-windowed", "search-recent-relevant"):
            if not query or query.strip() in ("*", "**", ".*"):
                return True, "wildcard_or_empty_query"
            if len(query.strip()) < 3:
                return True, "query_too_short"

        # Check for excessive limits
        limit = arguments.get("limit", 0) or arguments.get("max_results", 0) or arguments.get("max_samples", 0)
        if limit and limit > 200:
            return True, "excessive_result_limit"

        # Check for SQL injection patterns
        if query:
            sql_keywords = ["SELECT ", "DROP ", "DELETE ", "INSERT ", "UPDATE ", " FROM ", " WHERE "]
            query_upper = query.upper()
            for kw in sql_keywords:
                if kw in query_upper:
                    return True, "sql_injection_pattern"

        # Check for prompt injection patterns
        if query:
            injection_patterns = [
                "ignore previous", "system prompt", "you are now",
                "disregard", "forget your instructions",
            ]
            query_lower = query.lower()
            for pattern in injection_patterns:
                if pattern in query_lower:
                    return True, "prompt_injection_pattern"

        return False, ""

    async def _ollama_validate(self, tool_name: str, arguments: Dict[str, Any],
                               instance: str) -> Tuple[bool, str]:
        """Call Ollama to validate the request."""
        import httpx

        prompt = f"""You are a security validator for a screen recording search system.
Given the security policy and a tool request, respond with exactly one word: ALLOW or DENY.

SECURITY POLICY:
{self.policy}

TOOL REQUEST:
- Instance: {instance}
- Tool: {tool_name}
- Arguments: {json.dumps(arguments)}

Based on the policy, should this request be ALLOWED or DENIED?
Respond with exactly one word: ALLOW or DENY"""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ollama_host}/api/generate",
                    json={
                        "model": self.ollama_model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.0, "num_predict": 10},
                    },
                    timeout=self.timeout,
                )

                if response.status_code != 200:
                    logger.warning(f"Ollama returned {response.status_code}")
                    return False, "ollama_error"

                result = response.json()
                answer = result.get("response", "").strip().upper()

                if "ALLOW" in answer:
                    return True, "ai_allowed"
                else:
                    return False, f"ai_denied: {answer}"

        except httpx.TimeoutException:
            logger.warning("Ollama validation timed out")
            return False, "timeout_default_deny"
        except httpx.ConnectError:
            logger.warning("Cannot connect to Ollama - disabling AI validation")
            self.enabled = False
            return True, "ollama_unavailable_passthrough"
