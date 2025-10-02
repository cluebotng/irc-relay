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


async def main():
    logging.basicConfig(level=logging.INFO)
    runtime_config = RuntimeConfig.from_env()
    await send_via_udp(
        runtime_config.listener.address,
        runtime_config.listener.port,
        "#wikipedia-en-cbngfeed",
        "[[Type Dangerous]]  https://en.wikipedia.org/w/index.php?diff=1314252715&oldid=1313754858 * 2603:7081:1C00:534F:2199:A1F4:BA71:639E * (+0) /* Composition and lyrics */ # 0.041757 # Below threshold # Not reverted",
    )
    await send_via_udp(
        runtime_config.listener.address,
        runtime_config.listener.port,
        "#wikipedia-en-cbngfeed",
        "[[Spanish–American War]]  https://en.wikipedia.org/w/index.php?diff=1314252669&oldid=1310871853 * 50.216.6.66 * (-683)  # 0.779827 # Below threshold # Not reverted",
    )
    await send_via_udp(
        runtime_config.listener.address, runtime_config.listener.port, "#wikipedia-en-cbng-debug", "Hello World"
    )
    await send_via_tcp(
        runtime_config.listener.address, runtime_config.listener.port, "#wikipedia-en-cbng-debug", "Hello World"
    )


if __name__ == "__main__":
    asyncio.run(main())
