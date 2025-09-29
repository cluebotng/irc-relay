import dataclasses
import json
import os
from typing import List

from irc_relay.rate_limit import sliding_window


@dataclasses.dataclass
class SlidingWindowRateLimitConfig:
    buckets: List[sliding_window.BucketConfig]

    @staticmethod
    def from_default() -> "SlidingWindowRateLimitConfig":
        return SlidingWindowRateLimitConfig(
            buckets=[
                # 100 messages per 30 seconds
                sliding_window.BucketConfig(window=30, limit=100),
                # 5 messages per second
                sliding_window.BucketConfig(window=1, limit=5),
            ]
        )

    @staticmethod
    def from_environment() -> "SlidingWindowRateLimitConfig":
        if raw_config := os.environ.get("IRC_RELAY_LIMIT_SLIDING_WINDOW_CONFIG"):
            bucket_configs = json.loads(raw_config)
            return SlidingWindowRateLimitConfig(
                buckets=[
                    sliding_window.BucketConfig(window=bucket_config["window"], limit=bucket_config["limit"])
                    for bucket_config in bucket_configs
                ]
            )
        return SlidingWindowRateLimitConfig.from_default()
