import abc


class RateLimiter(abc.ABC):
    @abc.abstractmethod
    def should_allow(self) -> bool: ...
