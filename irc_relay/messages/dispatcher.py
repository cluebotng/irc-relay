import asyncio

from irc_relay.config.sender import CbngReceiverConfig, SenderConfig
from irc_relay.messages.models import Message, ProcessedEdit, TextMessage
from irc_relay.messages.processor import ClueBotNGMessageProcessor, StringHuggleMessageProcessor
from irc_relay.senders.irc import IrcClient


class MessageReceiver:
    async def send(self, message: Message) -> None:
        raise NotImplementedError


class EditMessageReceiver:
    async def send_edit(self, edit: ProcessedEdit) -> None:
        raise NotImplementedError


class IrcReceiver(MessageReceiver):
    def __init__(self, irc_client: IrcClient):
        self._irc_client = irc_client

    async def send(self, message: Message) -> None:
        await self._irc_client.send_to_channel(message.channel, message.string)


class HuggleIrcReceiver(IrcReceiver, StringHuggleMessageProcessor):
    async def send(self, message: Message) -> None:
        huggle_messages = await self._get_huggle_messages(message)
        await asyncio.gather(
            *[self._irc_client.send_to_channel(channel, msg) for channel, msg in huggle_messages]
        )


class ClueBotNGIrcReceiver(IrcReceiver, ClueBotNGMessageProcessor, EditMessageReceiver):
    def __init__(self, irc_client: IrcClient, cbng_config: CbngReceiverConfig):
        super().__init__(irc_client)
        self._cbng_config = cbng_config

    async def send_edit(self, edit: ProcessedEdit) -> None:
        messages = self._get_edit_messages(
            edit,
            revert_channel=self._cbng_config.revert_channel,
            huggle_channel=self._cbng_config.huggle_channel,
        )
        await asyncio.gather(
            *[self._irc_client.send_to_channel(channel, msg) for channel, msg in messages]
        )


class DebugReceiver(MessageReceiver, StringHuggleMessageProcessor, ClueBotNGMessageProcessor, EditMessageReceiver):
    async def send(self, message: Message) -> None:
        huggle_messages = await self._get_huggle_messages(message)
        print(f"[{message.channel}] {message.string}")
        print(huggle_messages)
        print("")

    async def send_edit(self, edit: ProcessedEdit) -> None:
        for channel, msg in self._get_edit_messages(
            edit, revert_channel="#debug-revert", huggle_channel="#debug-huggle"
        ):
            print(f"  [{channel}] {msg}")
        print("")


class MessageDispatcher:
    def __init__(self):
        self._receivers: list[MessageReceiver] = []

    def add_receiver(self, receiver: MessageReceiver) -> None:
        self._receivers.append(receiver)

    def remove_receiver(self, receiver: MessageReceiver) -> None:
        self._receivers.remove(receiver)

    async def send(self, message: Message) -> None:
        await asyncio.gather(*[receiver.send(message) for receiver in self._receivers])

    async def send_edit(self, edit: ProcessedEdit) -> None:
        edit_receivers = [r for r in self._receivers if isinstance(r, EditMessageReceiver)]
        await asyncio.gather(*[receiver.send_edit(edit) for receiver in edit_receivers])


def _make_receiver(receiver_type: str, client: IrcClient, sender_config: SenderConfig) -> MessageReceiver:
    if receiver_type == "irc":
        return IrcReceiver(client)
    if receiver_type == "huggle":
        return HuggleIrcReceiver(client)
    if receiver_type == "cbng":
        return ClueBotNGIrcReceiver(client, sender_config.cbng)
    raise ValueError(f"Unknown receiver type: {receiver_type}")
