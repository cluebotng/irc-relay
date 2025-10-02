import dataclasses
import logging
import os
from typing import List

from irc_relay.config.listener import ListenerConfig
from irc_relay.config.metrics import MetricsConfig
from irc_relay.config.sender import SenderConfig

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class RuntimeConfig:
    senders: List[SenderConfig]
    listener: ListenerConfig
    metrics: MetricsConfig

    @staticmethod
    def from_env() -> "RuntimeConfig":
        environments = set()
        for env_var in os.environ.keys():
            if env_var.startswith("IRC_RELAY_SENDER_"):
                environments.add(env_var.removeprefix("IRC_RELAY_SENDER_").split("_")[0].lower())

        logger.info(f"Found environments: {environments}")
        return RuntimeConfig(
            senders=[SenderConfig.from_env(environment) for environment in environments],
            listener=ListenerConfig.from_env(),
            metrics=MetricsConfig.from_env(),
        )
