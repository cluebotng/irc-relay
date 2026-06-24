import dataclasses
import os
from typing import Optional

from irc_relay.config.irc import IrcClientConfig
from irc_relay.config.rate_limit import SlidingWindowRateLimitConfig


@dataclasses.dataclass
class CbngReceiverConfig:
    revert_channel: Optional[str]
    huggle_channel: Optional[str]

    @staticmethod
    def from_environment(env_var_prefix: str) -> "CbngReceiverConfig":
        return CbngReceiverConfig(
            revert_channel=os.environ.get(f"{env_var_prefix}_REVERT_CHANNEL"),
            huggle_channel=os.environ.get(f"{env_var_prefix}_HUGGLE_CHANNEL"),
        )


@dataclasses.dataclass
class SenderConfig:
    receiver: str
    throttler: Optional[SlidingWindowRateLimitConfig]
    client: IrcClientConfig
    cbng: CbngReceiverConfig

    @staticmethod
    def from_env(name: str) -> "SenderConfig":
        env_key = "IRC_RELAY_SENDER"
        if name != "default":
            env_key += f"_{name.upper()}"

        return SenderConfig(
            receiver=os.environ.get(f"{env_key}_RECEIVER", "cbng"),
            throttler=SlidingWindowRateLimitConfig.from_environment(f"{env_key}_THROTTLER"),
            client=IrcClientConfig.from_environment(f"{env_key}_CLIENT"),
            cbng=CbngReceiverConfig.from_environment(f"{env_key}_CBNG"),
        )
