import dataclasses
import os
from typing import Optional, List


@dataclasses.dataclass
class IrcClientConfig:
    server: str
    port: int
    nick: str
    username: Optional[str]
    password: Optional[str]
    channels: List[str]

    @staticmethod
    def from_environment(env_var_prefix: str) -> "IrcClientConfig":
        return IrcClientConfig(
            server=os.environ.get(f"{env_var_prefix}_SERVER", "irc.libera.chat"),
            port=int(os.environ.get(f"{env_var_prefix}_PORT", "6697")),
            nick=os.environ.get(f"{env_var_prefix}_NICK", "CBNGRelay_Development"),
            username=os.environ.get(f"{env_var_prefix}_USERNAME"),
            password=os.environ.get(f"{env_var_prefix}_PASSWORD"),
            channels=[
                channel.strip()
                for channel in os.environ.get(f"{env_var_prefix}_CHANNELS", "").split(",")
                if channel.strip()
            ],
        )
