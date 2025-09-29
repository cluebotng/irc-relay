class RateLimiter:
    def should_allow(self) -> bool:
        raise NotImplementedError
