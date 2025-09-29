#!/usr/bin/env python3
import asyncio
import logging

from irc_relay.config.runtime import RuntimeConfig
from irc_relay.listeners.tcp import TcpListener
from irc_relay.messages.dispatcher import MessageDispatcher, IrcReceiver
from irc_relay.listeners.udp import UdpListener
from irc_relay.http_api.server import HttpServer
from irc_relay.rate_limit.sliding_window import SlidingWindowRateLimit
from irc_relay.senders.irc import IrcClient

logger = logging.getLogger(__name__)


async def main():
    logging.basicConfig(level=logging.INFO)
    runtime_config = RuntimeConfig.from_env()

    message_dispatcher = MessageDispatcher()
    rate_limiter = SlidingWindowRateLimit(runtime_config.throttler.buckets)

    irc_client = IrcClient(
        runtime_config.irc.server,
        runtime_config.irc.port,
        runtime_config.irc.nick,
        runtime_config.irc.username,
        runtime_config.irc.password,
        runtime_config.irc.channels,
        rate_limiter,
    )

    message_dispatcher.add_receiver(IrcReceiver(irc_client))

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

    run_udp_listener = asyncio.create_task(udp_listener.run())
    run_tcp_listener = asyncio.create_task(tcp_listener.run())
    run_http_server = asyncio.create_task(run_http_server.run())
    run_irc_client = asyncio.create_task(irc_client.run())

    await asyncio.gather(run_udp_listener, run_tcp_listener, run_irc_client, run_http_server)


if __name__ == "__main__":
    asyncio.run(main())
