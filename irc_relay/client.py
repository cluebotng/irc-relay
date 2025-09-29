#!/usr/bin/env python3
import asyncio
import logging

import asyncudp

from irc_relay.config.runtime import RuntimeConfig


async def send_via_udp(address: str, port: int, channel: str, message: str) -> None:
    s = await asyncudp.create_socket(remote_addr=(address, port))
    s.sendto(f"{channel}:{message}".encode("utf-8"))
    s.close()


async def send_via_tcp(address: str, port: int, channel: str, message: str) -> None:
    _, writer = await asyncio.open_connection(address, port)
    writer.write(f"{channel}:{message}".encode("utf-8"))
    await writer.drain()
    writer.close()
    await writer.wait_closed()


async def main(channel: str = "#wikipedia-en-cbng-debug", message: str = "Hello World"):
    logging.basicConfig(level=logging.INFO)
    runtime_config = RuntimeConfig.from_env()
    await send_via_udp(runtime_config.listener.address, runtime_config.listener.port, channel, message)
    await send_via_tcp(runtime_config.listener.address, runtime_config.listener.port, channel, message)


if __name__ == "__main__":
    asyncio.run(main())
