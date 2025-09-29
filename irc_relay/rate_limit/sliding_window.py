import dataclasses
import logging
import time
from typing import List

from irc_relay.rate_limit.base import RateLimiter

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class BucketConfig:
    limit: int
    window: int

    def __hash__(self) -> hash:
        return hash((self.window, self.limit))


class SlidingWindowRateLimit(RateLimiter):
    def __init__(self, buckets: List[BucketConfig]) -> None:
        # Explicitly sort the buckets, so we evaluate the smallest window first
        self._buckets = sorted(buckets, key=lambda b: b.window)
        self._windows = {bucket: [] for bucket in buckets}

    def _bucket_has_capacity(self, bucket: BucketConfig):
        current_period = time.time() - bucket.window

        # Remove any entries that are older than our window
        while self._windows[bucket] and self._windows[bucket][0] < current_period:
            self._windows[bucket].pop()

        # Check if we have any space
        current_usage = len(self._windows[bucket])
        if current_usage <= bucket.limit:
            self._windows[bucket].append(time.time())
            return True

        print(f"Bucket {bucket} has no capacity {current_usage}")
        return False

    def should_allow(self) -> bool:
        return all([self._bucket_has_capacity(bucket) for bucket in self._buckets])
