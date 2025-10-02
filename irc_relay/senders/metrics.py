from prometheus_client import Counter, Gauge

from irc_relay.config import PROMETHEUS_METRIC_NAMESPACE

irc_messages_rejected = Counter(
    f"{PROMETHEUS_METRIC_NAMESPACE}_irc_messages_rejected",
    "Number of messages rejected by the sender",
    ["name", "reason", "channel"],
)

irc_messages_accepted = Counter(
    f"{PROMETHEUS_METRIC_NAMESPACE}_irc_messages_accepted",
    "Number of messages accepted by the sender",
    ["name", "channel"],
)

irc_connection_status = Gauge(
    f"{PROMETHEUS_METRIC_NAMESPACE}_irc_connection_status",
    "Connection status",
    ["name"],
)

irc_connection_time = Gauge(
    f"{PROMETHEUS_METRIC_NAMESPACE}_irc_connection_time",
    "Last connection time",
    ["name"],
)
