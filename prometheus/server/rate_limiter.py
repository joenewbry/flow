#!/usr/bin/env python3
"""
Rate limiter for Memex Prometheus Server.

In-memory sliding window rate limiter.
- Per IP: 60 req/min, 500 req/hour
- Per instance: 120 req/min total
"""

import logging
import time
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class SlidingWindowCounter:
    """Sliding window rate limiter."""

    def __init__(self):
        self.requests: Dict[str, List[float]] = defaultdict(list)

    def _cleanup(self, key: str, window_seconds: int):
        """Remove expired entries."""
        cutoff = time.time() - window_seconds
        self.requests[key] = [t for t in self.requests[key] if t > cutoff]

    def check_and_record(self, key: str, window_seconds: int, max_requests: int) -> Tuple[bool, int]:
        """
        Check if request is allowed and record it.

        Returns:
            (allowed, retry_after_seconds)
        """
        self._cleanup(key, window_seconds)

        if len(self.requests[key]) >= max_requests:
            # Calculate retry-after
            oldest = self.requests[key][0] if self.requests[key] else time.time()
            retry_after = int(oldest + window_seconds - time.time()) + 1
            return False, max(1, retry_after)

        self.requests[key].append(time.time())
        return True, 0

    def get_count(self, key: str, window_seconds: int) -> int:
        """Get current request count in window."""
        self._cleanup(key, window_seconds)
        return len(self.requests[key])


class RateLimiter:
    """Multi-tier rate limiter for the Memex server."""

    def __init__(self, ip_per_minute: int = 60, ip_per_hour: int = 500,
                 instance_per_minute: int = 120):
        self.ip_per_minute = ip_per_minute
        self.ip_per_hour = ip_per_hour
        self.instance_per_minute = instance_per_minute
        self.counter = SlidingWindowCounter()

    def check(self, client_ip: str, instance: str) -> Tuple[bool, Optional[int], Optional[str]]:
        """
        Check rate limits for a request.

        Returns:
            (allowed, retry_after_seconds, limit_type_exceeded)
        """
        # Check per-IP per-minute limit
        ip_min_key = f"ip_min:{client_ip}"
        allowed, retry_after = self.counter.check_and_record(ip_min_key, 60, self.ip_per_minute)
        if not allowed:
            logger.warning(f"Rate limit exceeded: IP {client_ip} per-minute ({self.ip_per_minute}/min)")
            return False, retry_after, "ip_per_minute"

        # Check per-IP per-hour limit
        ip_hour_key = f"ip_hour:{client_ip}"
        allowed, retry_after = self.counter.check_and_record(ip_hour_key, 3600, self.ip_per_hour)
        if not allowed:
            logger.warning(f"Rate limit exceeded: IP {client_ip} per-hour ({self.ip_per_hour}/hr)")
            return False, retry_after, "ip_per_hour"

        # Check per-instance per-minute limit
        inst_key = f"inst_min:{instance}"
        allowed, retry_after = self.counter.check_and_record(inst_key, 60, self.instance_per_minute)
        if not allowed:
            logger.warning(f"Rate limit exceeded: instance {instance} per-minute ({self.instance_per_minute}/min)")
            return False, retry_after, "instance_per_minute"

        return True, None, None
