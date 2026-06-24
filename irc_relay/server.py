#!/usr/bin/env python3
import asyncio
import logging

from irc_relay.config.runtime import RuntimeConfig
from irc_relay.http_api.server import HttpServer
from irc_relay.rate_limit.sliding_window import SlidingWindowRateLimit
from irc_relay.messages.dispatcher import (
    MessageDispatcher,
    DebugReceiver,
    make_receiver,
)
from irc_relay.senders.irc import IrcClient

logger = logging.getLogger(__name__)


async def main():
    logging.basicConfig(level=logging.INFO)
    runtime_config = RuntimeConfig.from_env()
    message_dispatcher = MessageDispatcher()

    jobs = [
        asyncio.create_task(
            HttpServer(runtime_config.metrics.address, runtime_config.metrics.port, message_dispatcher).run()
        ),
    ]

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
        message_dispatcher.add_receiver(make_receiver(sender.receiver, client, sender))

    if not runtime_config.senders:
        logger.info("Adding default debug receiver")
        message_dispatcher.add_receiver(DebugReceiver())

    await asyncio.gather(*jobs)


if __name__ == "__main__":
    asyncio.run(main())
