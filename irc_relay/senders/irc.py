import asyncio
import base64
import logging
import time
from typing import Optional, List, Dict

import bottom

from irc_relay.rate_limit.base import RateLimiter
from irc_relay.senders.metrics import (
    irc_messages_accepted,
    irc_messages_rejected,
    irc_connection_status,
    irc_connection_time,
)

logger = logging.getLogger(__name__)


class IrcClient:
    _should_run: bool
    _can_accept_messages: Dict[str, bool]
    _allowed_channels: List[str]
    _client: Optional[bottom.Client]

    def __init__(
        self,
        server: str,
        port: int,
        nick: str,
        username: Optional[str],
        password: Optional[str],
        allowed_channels: List[str],
        rate_limiter: Optional[RateLimiter],
    ):
        self._identifier = f"{server}:{port}"

        self._can_accept_messages = {channel.lower(): False for channel in allowed_channels}
        self._should_run = True
        self._rate_limiter = rate_limiter

        self._allowed_channels = [channel.lower() for channel in allowed_channels]
        self._irc_nick = nick
        self._irc_username = username
        self._irc_password = password

        self._client = bottom.Client(host=server, port=port, ssl=(port == 6697))

        # Deal with SASL messages not handled by rfc2812_handler
        self._client.message_handlers.insert(0, self._sasl_message_handler)

        # Dump all messages if we are debugging
        if logger.getEffectiveLevel() == logging.DEBUG:
            self._client.message_handlers.append(self._debug_message_handler)

        # Callbacks
        self._client.on("CLIENT_CONNECT")(self._connect_callback)
        self._client.on("PING")(self._ping_callback)
        self._client.on("PRIVMSG")(self._message_callback)

    async def send_to_channel(self, channel: str, string: str) -> None:
        channel = channel.lower()
        if channel not in self._allowed_channels:
            logger.debug(f"[{self._identifier}] {channel} is not in allowed channels, ignoring")
            irc_messages_rejected.labels(name=self._identifier, channel=channel, reason="missing_in_allowed").inc()
            return

        if not self._can_accept_messages[channel]:
            logger.warning(f"[{self._identifier}] {channel} can not accept messages, ignoring")
            irc_messages_rejected.labels(name=self._identifier, channel=channel, reason="not_joined").inc()
            return

        if self._rate_limiter and not self._rate_limiter.should_allow():
            logger.warning(f"[{self._identifier}] [{channel}] dropping due to rate limit: {string}")
            irc_messages_rejected.labels(name=self._identifier, channel=channel, reason="rate_limit").inc()
            return

        logger.info(f"Sending [{channel}] {string}")
        await self._client.send("privmsg", target=channel, message=string)
        irc_messages_accepted.labels(name=self._identifier, channel=channel).inc()

    async def shutdown(self):
        logger.info(f"[{self._identifier}] Shutting down IRC Client")
        self._should_run = False
        if self._client:
            await self._client.disconnect()

    async def _sasl_message_handler(
        self, next_handler: bottom.NextMessageHandler[bottom.Client], client: bottom.Client, message: bytes
    ) -> None:
        # Add SASL support
        parts = message.decode().split(" ")

        # Need at least `:<server> <message>` or `AUTHENTICATE +`
        if len(parts) >= 2:
            # Response to `CAP REQ sasl`, first item is `:<server>`
            if parts[1:4] == ["CAP", "*", "ACK"]:
                parts[4] = parts[4].removeprefix(":")
                client.trigger("CAP_ACK", capabilities=parts[4:])
                return

            # Response to `AUTHENTICATE PLAIN`
            if parts == ["AUTHENTICATE", "+"]:
                client.trigger("SASL_AUTHENTICATION_REQUEST")
                return

            if parts[1] == "900":
                parts[4] = parts[4].removeprefix(":")
                client.trigger("SASL_USER_LOGGED_IN", code="RPL_LOGGEDIN", message=parts[4:])
                return

            if parts[1] == "903":
                parts[4] = parts[4].removeprefix(":")
                client.trigger("SASL_AUTHENTICATION_SUCCESS", code="RPL_SASLSUCCESS", message=parts[4:])
                return

            if parts[1] == "904":
                client.trigger("SASL_AUTHENTICATION_FAILED", code="ERR_SASLFAIL", message=parts[4:])
                return

        await next_handler(client, message)

    async def _debug_message_handler(
        self, next_handler: bottom.NextMessageHandler[bottom.Client], client: bottom.Client, message: bytes
    ) -> None:
        # For debugging only, prefer to use callbacks
        logger.debug(f"[{self._identifier}] Received: {message.decode()}")
        await next_handler(client, message)

    async def _ping_callback(self, message: str, **kwargs) -> None:
        await self._client.send("pong", message=message)

    async def _message_callback(self, nick: str, target: str, message: str, **kwargs) -> None:
        logger.info(f"[{self._identifier}] Got message from {nick} in {target: {message}}")

    async def _authenticate_via_sasl(self) -> bool:
        if not (self._irc_username and self._irc_password):
            logger.info(f"[{self._identifier}] No credentials, skipping SASL")
            return True

        # Ask to do SASL
        logger.debug(f"[{self._identifier}] Requesting SASL capabilities")
        await self._client.send_message("CAP REQ sasl")

        response = (await bottom.wait_for(self._client, ["CAP_ACK"], mode="first"))[0]
        capabilities = response.get("capabilities", [])
        if "sasl" not in capabilities:
            logger.error(f"[{self._identifier}] Server did not agree to SASL: {capabilities}")
            return False

        logger.debug(f"[{self._identifier}] Server agreed to capabilities: {response}")

        # Ask to start authentication
        logger.debug("Asking server to authenticate")
        await self._client.send_message("AUTHENTICATE PLAIN")

        # Server wants credentials
        await bottom.wait_for(self._client, ["SASL_AUTHENTICATION_REQUEST"], mode="first")
        logger.debug(f"[{self._identifier}] Server requested authentication")

        # Send credentials
        auth_string = base64.b64encode(
            f"{self._irc_nick}\0{self._irc_username}\0{self._irc_password}".encode("utf-8")
        ).decode("utf-8")
        logger.debug(f"[{self._identifier}] Sending authentication")
        await self._client.send_message(f"AUTHENTICATE {auth_string}")

        response = await bottom.wait_for(
            self._client, ["SASL_AUTHENTICATION_SUCCESS", "SASL_AUTHENTICATION_FAILED"], mode="first"
        )
        for message in response:
            if message.get("__event__") == "SASL_AUTHENTICATION_SUCCESS":
                logger.debug("SASL authentication succeeded, ending capabilities")
                await self._client.send_message("CAP END")
                return True

            if message.get("__event__") == "SASL_AUTHENTICATION_FAILED":
                logger.error(f"SASL authentication failed: {message}")

        return False

    async def _connect_callback(self, **kwargs) -> None:
        logger.debug(f"[{self._identifier}] Connected to IRC")
        irc_connection_status.labels(name=self._identifier).set(1)
        irc_connection_time.labels(name=self._identifier).set(time.time())

        if not await self._authenticate_via_sasl():
            logger.error(f"[{self._identifier}] SASL failed")
            irc_connection_status.labels(name=self._identifier).set(0)
            await self._client.disconnect()
            return

        logger.debug(f"[{self._identifier}] Sending registration details ({self._irc_nick})")
        await self._client.send("nick", nick=self._irc_nick)
        await self._client.send(
            "user",
            nick=self._irc_nick,
            realname="ClueBot NG IRC Relay",
        )
        await self._client.send_message(f"MODE {self._irc_nick} +B")

        logger.debug(f"[{self._identifier}] Waiting for end of MOTD before joining channels")
        await bottom.wait_for(self._client, ["RPL_ENDOFMOTD", "ERR_NOMOTD"], mode="first")

        logger.info(f"[{self._identifier}] Joining channels: {self._allowed_channels}")
        for channel in self._allowed_channels:
            await self._client.send("join", channel=channel)
            self._can_accept_messages[channel] = True

    async def run(self) -> None:
        logger.info(f"[{self._identifier}] Starting IRC Client")
        while self._should_run:
            await self._client.connect()
            await self._client.wait("client_disconnect")
            logger.error(f"[{self._identifier}] Disconnected by remote")

            irc_connection_status.labels(name=self._identifier).set(0)
            self._can_accept_messages = {channel: False for channel in self._can_accept_messages.keys()}
            await asyncio.sleep(5)
