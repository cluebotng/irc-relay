import collections
import dataclasses
import logging
import time

from irc_relay.rate_limit.base import RateLimiter

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class BucketConfig:
    limit: int
    window: int

    def __hash__(self) -> int:
        return hash((self.window, self.limit))


class SlidingWindowRateLimit(RateLimiter):
    def __init__(self, buckets: list[BucketConfig]) -> None:
        # Explicitly sort the buckets, so we evaluate the smallest window first
        self._buckets = sorted(buckets, key=lambda b: b.window)
        self._windows: dict[BucketConfig, collections.deque[float]] = {
            bucket: collections.deque() for bucket in buckets
        }

    def _bucket_has_capacity(self, bucket: BucketConfig) -> bool:
        current_period = time.time() - bucket.window

        # Remove entries older than our window
        while self._windows[bucket] and self._windows[bucket][0] < current_period:
            self._windows[bucket].popleft()

        if len(self._windows[bucket]) < bucket.limit:
            self._windows[bucket].append(time.time())
            return True
        return False

    def should_allow(self) -> bool:
        return all(self._bucket_has_capacity(bucket) for bucket in self._buckets)
