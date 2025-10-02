#!/usr/bin/env python3
import asyncio
import logging

from irc_relay.config.runtime import RuntimeConfig
from irc_relay.http_api.server import HttpServer
from irc_relay.listeners.tcp import TcpListener
from irc_relay.listeners.udp import UdpListener
from irc_relay.rate_limit.sliding_window import SlidingWindowRateLimit
from irc_relay.messages.dispatcher import (
    MessageDispatcher,
    DebugReceiver,
    SUPPORTED_RECEIVERS,
)
from irc_relay.senders.irc import IrcClient

logger = logging.getLogger(__name__)


async def main():
    logging.basicConfig(level=logging.INFO)
    runtime_config = RuntimeConfig.from_env()
    message_dispatcher = MessageDispatcher()

    udp_listener = UdpListener(
        runtime_config.listener.address,
        runtime_config.listener.port,
        message_dispatcher,
    )

    tcp_listener = TcpListener(
        runtime_config.listener.address,
        runtime_config.listener.port,
        message_dispatcher,
    )

    run_http_server = HttpServer(
        runtime_config.metrics.address,
        runtime_config.metrics.port,
        message_dispatcher,
    )

    # Start the listeners
    jobs = [
        asyncio.create_task(udp_listener.run()),
        asyncio.create_task(tcp_listener.run()),
        asyncio.create_task(run_http_server.run()),
    ]

    # Start the senders
    for sender in runtime_config.senders:
        logger.info(f"Creating sender: {sender.client.server}:{sender.client.port}")
        client = IrcClient(
            sender.client.server,
            sender.client.port,
            sender.client.nick,
            sender.client.username,
            sender.client.password,
            sender.client.channels,
            SlidingWindowRateLimit(sender.throttler.buckets) if sender.throttler else None,
        )
        jobs.append(asyncio.create_task(client.run()))
        message_dispatcher.add_receiver(SUPPORTED_RECEIVERS[sender.receiver](client))

    # Create a default message receiver if we have no senders
    if not runtime_config.senders:
        logger.info("Adding default debug receiver")
        message_dispatcher.add_receiver(DebugReceiver())

    await asyncio.gather(*jobs)


if __name__ == "__main__":
    asyncio.run(main())
