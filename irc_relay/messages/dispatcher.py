import asyncio

from irc_relay.messages.models import Message
from irc_relay.messages.processor import HuggleMessageProcessor
from irc_relay.senders.irc import IrcClient


class MessageReceiver:
    def send(self, message: Message) -> None:
        raise NotImplementedError


class IrcReceiver(MessageReceiver):
    def __init__(self, irc_client: IrcClient):
        self._irc_client = irc_client

    async def send(self, message: Message) -> None:
        await self._irc_client.send_to_channel(message.channel, message.string)


class HuggleIrcReceiver(IrcReceiver, HuggleMessageProcessor):
    async def send(self, message: Message) -> None:
        huggle_messages = await self._get_huggle_messages(message)
        await asyncio.gather(
            *[self._irc_client.send_to_channel(channel, message) for channel, message in huggle_messages]
        )


class DebugReceiver(MessageReceiver, HuggleMessageProcessor):
    async def send(self, message: Message) -> None:
        huggle_messages = await self._get_huggle_messages(message)
        print(f"[{message.channel}] {message.string}")
        print(huggle_messages)
        print("")


class MessageDispatcher:
    def __init__(self):
        self._receivers = []

    def add_receiver(self, receiver: MessageReceiver):
        self._receivers.append(receiver)

    def remove_receiver(self, receiver: MessageReceiver):
        self._receivers.remove(receiver)

    async def send(self, message: Message) -> None:
        await asyncio.gather(*[receiver.send(message) for receiver in self._receivers])


SUPPORTED_RECEIVERS = {
    "irc": IrcReceiver,
    "huggle": HuggleIrcReceiver,
}
