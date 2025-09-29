import dataclasses

from irc_relay.config.irc import IrcClientConfig
from irc_relay.config.metrics import MetricsConfig
from irc_relay.config.rate_limit import SlidingWindowRateLimitConfig
from irc_relay.config.listener import ListenerConfig


@dataclasses.dataclass
class RuntimeConfig:
    irc: IrcClientConfig
    listener: ListenerConfig
    metrics: MetricsConfig
    throttler: SlidingWindowRateLimitConfig

    @staticmethod
    def from_env() -> "RuntimeConfig":
        return RuntimeConfig(
            irc=IrcClientConfig.from_env(),
            listener=ListenerConfig.from_env(),
            metrics=MetricsConfig.from_env(),
            throttler=SlidingWindowRateLimitConfig.from_environment(),
        )
