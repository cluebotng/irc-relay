import dataclasses
import os


@dataclasses.dataclass
class MetricsConfig:
    address: str
    port: int

    @staticmethod
    def from_env() -> "MetricsConfig":
        return MetricsConfig(
            address=os.environ.get("IRC_RELAY_METRICS_ADDRESS", "0.0.0.0"),  # nosec B104:hardcoded_bind_all_interfaces
            port=int(os.environ.get("IRC_RELAY_METRICS_PORT", "9334")),
        )
