import dataclasses
import os


@dataclasses.dataclass
class ListenerConfig:
    address: str
    port: int

    @staticmethod
    def from_env() -> "ListenerConfig":
        return ListenerConfig(
            address=os.environ.get("IRC_RELAY_LISTEN_ADDRESS", "0.0.0.0"),  # nosec B104:hardcoded_bind_all_interfaces
            port=int(os.environ.get("IRC_RELAY_LISTEN_PORT", "3334")),
        )
