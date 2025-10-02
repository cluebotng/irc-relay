from freezegun import freeze_time

from irc_relay.rate_limit.sliding_window import SlidingWindowRateLimit, BucketConfig


class TestSlidingWindowRateLimit:

    @freeze_time()
    def test_single_bucket(self):
        rate_limiter = SlidingWindowRateLimit([BucketConfig(window=1, limit=25)])
        for x in range(0, 50):
            if x <= 25:
                assert rate_limiter.should_allow() is True  # nosec B101:assert_used
            else:
                assert rate_limiter.should_allow() is False  # nosec B101:assert_used

    def test_multi_bucket(self):
        rate_limiter = SlidingWindowRateLimit([BucketConfig(window=1, limit=25), BucketConfig(window=30, limit=100)])

        # 1 second bucket should allow half
        with freeze_time("2025-09-01 00:00:00"):
            for x in range(0, 51):
                if x <= 25:
                    assert rate_limiter.should_allow() is True, f"Instance {x}"  # nosec B101:assert_used
                else:
                    assert rate_limiter.should_allow() is False, f"Instance {x}"  # nosec B101:assert_used

        # 30 second bucket should allow half, it already has half from the above
        # Progress the second to avoid the 1 second bucket
        instance = 0
        for s in range(1, 11):
            with freeze_time(f"2025-09-01 00:00:{10 + s}"):
                for x in range(0, 10):
                    instance += 1
                    if instance <= 50:
                        assert rate_limiter.should_allow() is True, f"Instance {instance}"  # nosec B101:assert_used
                    else:
                        assert rate_limiter.should_allow() is False, f"Instance {instance}"  # nosec B101:assert_used
