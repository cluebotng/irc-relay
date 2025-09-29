import logging

import asyncudp

from irc_relay.messages.dispatcher import MessageDispatcher
from irc_relay.messages.models import Message

logger = logging.getLogger(__name__)


class UdpListener:
    def __init__(self, address: str, port: int, dispatcher: MessageDispatcher):
        self._should_run = True
        self._address = address
        self._port = port
        self._dispatcher = dispatcher

    async def shutdown(self):
        logger.info("Shutting down UDP Listener")
        self._should_run = False

    async def run(self) -> None:
        logger.info("Starting UDP Listener")
        sock = await asyncudp.create_socket(local_addr=(self._address, self._port))
        while self._should_run:
            data, _ = await sock.recvfrom()
            parts = data.decode("utf-8").split(":")
            if len(parts) >= 2:
                await self._dispatcher.send(Message(channel=parts[0], string=":".join(parts[1:])))
            else:
                logger.error(f"Invalid message received: {data}")

        sock.close()
