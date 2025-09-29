from prometheus_client import Counter

from irc_relay.config import PROMETHEUS_METRIC_NAMESPACE

listener_messages_rejected = Counter(
    f"{PROMETHEUS_METRIC_NAMESPACE}_listener_messages_rejected",
    "Number of messages rejected by the listener",
    ["listener"],
)

listener_messages_accepted = Counter(
    f"{PROMETHEUS_METRIC_NAMESPACE}_listener_messages_accepted",
    "Number of messages accepted by the listener",
    ["listener"],
)
