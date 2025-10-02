import dataclasses
import os
from typing import Optional

from irc_relay.config.irc import IrcClientConfig
from irc_relay.config.rate_limit import SlidingWindowRateLimitConfig


@dataclasses.dataclass
class SenderConfig:
    receiver: str
    throttler: Optional[SlidingWindowRateLimitConfig]
    client: IrcClientConfig

    @staticmethod
    def from_env(name: str) -> "SenderConfig":
        env_key = "IRC_RELAY_SENDER"
        if name != "default":
            env_key += f"_{name.upper()}"

        return SenderConfig(
            receiver=os.environ.get(f"{env_key}_RECEIVER", "irc"),
            throttler=SlidingWindowRateLimitConfig.from_environment(f"{env_key}_THROTTLER"),
            client=IrcClientConfig.from_environment(f"{env_key}_CLIENT"),
        )
