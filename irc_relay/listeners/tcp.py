import asyncio
import logging

from irc_relay.listeners.metrics import listener_messages_accepted, listener_messages_rejected
from irc_relay.messages.dispatcher import MessageDispatcher
from irc_relay.messages.models import Message

logger = logging.getLogger(__name__)


class TcpListener:
    def __init__(self, address: str, port: int, dispatcher: MessageDispatcher):
        self._should_run = True
        self._address = address
        self._port = port
        self._dispatcher = dispatcher
        self._server = None

    async def shutdown(self):
        logger.info("Shutting down UDP Listener")
        self._should_run = False
        if self._server:
            self._server.close()

    async def _handle(self, reader, writer):
        if data := await reader.read(512):
            parts = data.decode("utf-8").split(":")
            if len(parts) >= 2:
                await self._dispatcher.send(Message(channel=parts[0], string=":".join(parts[1:])))
                listener_messages_accepted.labels(listener="tcp").inc()
            else:
                logger.error(f"Invalid message received: {data}")
                listener_messages_rejected.labels(listener="tcp").inc()

    async def run(self) -> None:
        logger.info("Starting TCP Listener")

        self._server = await asyncio.start_server(self._handle, self._address, self._port)
        async with self._server:
            await self._server.serve_forever()
