import abc
import asyncio

from irc_relay.config.sender import CbngReceiverConfig, SenderConfig
from irc_relay.messages.models import ProcessedEdit, TextMessage, WarnedUser
from irc_relay.messages.processor import ClueBotNGMessageProcessor
from irc_relay.senders.irc import IrcClient


class MessageReceiver(abc.ABC):
    @abc.abstractmethod
    async def send(self, message: TextMessage) -> None: ...


class EditMessageReceiver(abc.ABC):
    @abc.abstractmethod
    async def send_edit(self, edit: ProcessedEdit) -> None: ...


class WarnedUserReceiver(abc.ABC):
    @abc.abstractmethod
    async def send_user_warning(self, warn: WarnedUser) -> None: ...


class IrcReceiver(MessageReceiver):
    def __init__(self, irc_client: IrcClient):
        self._irc_client = irc_client

    async def send(self, message: TextMessage) -> None:
        await self._irc_client.send_to_channel(message.channel, message.string)


class ClueBotNGIrcReceiver(IrcReceiver, ClueBotNGMessageProcessor, EditMessageReceiver, WarnedUserReceiver):
    def __init__(self, irc_client: IrcClient, cbng_config: CbngReceiverConfig):
        super().__init__(irc_client)
        self._cbng_config = cbng_config

    async def send_edit(self, edit: ProcessedEdit) -> None:
        messages = self._get_edit_messages(
            edit,
            revert_channel=self._cbng_config.revert_channel,
            huggle_channel=self._cbng_config.huggle_channel,
        )
        await asyncio.gather(*[self._irc_client.send_to_channel(channel, msg) for channel, msg in messages])

    async def send_user_warning(self, warn: WarnedUser) -> None:
        messages = self._get_warn_messages(warn, huggle_channel=self._cbng_config.huggle_channel)
        await asyncio.gather(*[self._irc_client.send_to_channel(channel, msg) for channel, msg in messages])


class DebugReceiver(MessageReceiver, ClueBotNGMessageProcessor, EditMessageReceiver, WarnedUserReceiver):
    async def send(self, message: TextMessage) -> None:
        print(f"[{message.channel}] {message.string}")

    async def send_edit(self, edit: ProcessedEdit) -> None:
        for channel, msg in self._get_edit_messages(
            edit, revert_channel="#debug-revert", huggle_channel="#debug-huggle"
        ):
            print(f"  [{channel}] {msg}")
        print("")

    async def send_user_warning(self, warn: WarnedUser) -> None:
        for channel, msg in self._get_warn_messages(warn, huggle_channel="#debug-huggle"):
            print(f"  [{channel}] {msg}")
        print("")


class MessageDispatcher:
    def __init__(self):
        self._receivers: list[MessageReceiver] = []

    def add_receiver(self, receiver: MessageReceiver) -> None:
        self._receivers.append(receiver)

    def remove_receiver(self, receiver: MessageReceiver) -> None:
        self._receivers.remove(receiver)

    async def send(self, message: TextMessage) -> None:
        await asyncio.gather(*[receiver.send(message) for receiver in self._receivers])

    async def send_edit(self, edit: ProcessedEdit) -> None:
        edit_receivers = [r for r in self._receivers if isinstance(r, EditMessageReceiver)]
        await asyncio.gather(*[receiver.send_edit(edit) for receiver in edit_receivers])

    async def send_user_warning(self, warn: WarnedUser) -> None:
        warn_receivers = [r for r in self._receivers if isinstance(r, WarnedUserReceiver)]
        await asyncio.gather(*[receiver.send_user_warning(warn) for receiver in warn_receivers])


def make_receiver(receiver_type: str, client: IrcClient, sender_config: SenderConfig) -> MessageReceiver:
    if receiver_type == "irc":
        return IrcReceiver(client)
    if receiver_type == "cbng":
        return ClueBotNGIrcReceiver(client, sender_config.cbng)
    raise ValueError(f"Unknown receiver type: {receiver_type}")
