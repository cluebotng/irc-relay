import logging

import uvicorn
from fastapi import FastAPI, APIRouter, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from pydantic import BaseModel

from irc_relay.listeners.metrics import listener_messages_accepted
from irc_relay.messages.dispatcher import MessageDispatcher
from irc_relay.messages.models import EditChange, ProcessedEdit, TextMessage, WarnedUser

logger = logging.getLogger(__name__)
app = FastAPI()


class ExternalMessage(BaseModel):
    channel: str
    string: str


class EditChangePayload(BaseModel):
    title: str
    user: str
    url: str
    revision_id: int
    namespace: str = ""
    flags: list[str] = []
    length: str | None = None
    comment: str = ""


class EditPayload(BaseModel):
    change: EditChangePayload
    reverted: bool
    comment: str | None
    score: float | None


class WarnedUserPayload(BaseModel):
    username: str
    level: int


@app.get("/health")
async def _handle_health() -> Response:
    return Response("OK")


@app.get("/metrics")
async def _handle_metrics() -> Response:
    return Response(content=generate_latest(), headers={"Content-Type": CONTENT_TYPE_LATEST})


def create_listener(message_dispatcher: MessageDispatcher) -> APIRouter:
    router = APIRouter()

    @router.put("/")
    async def _handle_message(payload: ExternalMessage | EditPayload | WarnedUserPayload) -> Response:
        if isinstance(payload, ExternalMessage):
            await message_dispatcher.send(TextMessage(channel=payload.channel, string=payload.string))
        elif isinstance(payload, WarnedUserPayload):
            await message_dispatcher.send_user_warning(WarnedUser(username=payload.username, level=payload.level))
        else:
            await message_dispatcher.send_edit(
                ProcessedEdit(
                    change=EditChange(**payload.change.model_dump()),
                    score=payload.score,
                    reverted=payload.reverted,
                    comment=payload.comment,
                )
            )
        listener_messages_accepted.inc()
        return Response("OK")

    return router


class HttpServer:
    def __init__(self, address: str, port: int, dispatcher: MessageDispatcher):
        self._address = address
        self._port = port
        self._server: uvicorn.Server | None = None
        self._dispatcher = dispatcher

    async def shutdown(self) -> None:
        logger.info("Shutting down HTTP Server")
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
