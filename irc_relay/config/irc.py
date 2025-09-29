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
    def from_env() -> "IrcClientConfig":
        return IrcClientConfig(
            server=os.environ.get("IRC_RELAY_CLIENT_SERVER", "irc.libera.chat"),
            port=int(os.environ.get("IRC_RELAY_CLIENT_PORT", "6697")),
            nick=os.environ.get("IRC_RELAY_CLIENT_NICK", "CBNGRelay_Development"),
            username=os.environ.get("IRC_RELAY_CLIENT_USERNAME", "CBNGRelay_Development"),
            password=os.environ.get("IRC_RELAY_CLIENT_PASSWORD"),
            channels=[
                channel.strip()
                for channel in os.environ.get("IRC_RELAY_CLIENT_CHANNELS", "").split(",")
                if channel.strip()
            ],
        )
