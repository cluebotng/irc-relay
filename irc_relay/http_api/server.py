import logging

import uvicorn
from fastapi import FastAPI, APIRouter, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from pydantic import BaseModel

from irc_relay.listeners.metrics import listener_messages_accepted
from irc_relay.messages.dispatcher import MessageDispatcher
from irc_relay.messages.models import Message

logger = logging.getLogger(__name__)
app = FastAPI()


class ExternalMessage(BaseModel):
    channel: str
    string: str


@app.get("/health")
async def _handle_health() -> Response:
    return Response("OK")


@app.get("/metrics")
async def _handle_metrics() -> Response:
    return Response(content=generate_latest(), headers={"Content-Type": CONTENT_TYPE_LATEST})


def create_listener(message_dispatcher: MessageDispatcher) -> APIRouter:
    router = APIRouter()

    @router.put("/")
    async def _handle_message(message: ExternalMessage) -> Response:
        await message_dispatcher.send(Message(channel=message.channel, string=message.string))
        listener_messages_accepted.labels(listener="http").inc()
        return Response("OK")

    return router


class HttpServer:
    def __init__(self, address: str, port: int, dispatcher: MessageDispatcher):
        self._should_run = True
        self._address = address
        self._port = port
        self._server = None
        self._dispatcher = dispatcher

    async def shutdown(self):
        logger.info("Shutting down HTTP Server")
        self._should_run = False
        if self._server:
            self._server.shutdown()

    async def run(self) -> None:
        logger.info("Starting HTTP Server")
        app.include_router(create_listener(self._dispatcher))

        self._server = uvicorn.Server(
            uvicorn.Config(
                app,
                host=self._address,
                port=self._port,
                log_level="debug" if logger.getEffectiveLevel() == logging.DEBUG else "info",
            )
        )
        await self._server.serve()
