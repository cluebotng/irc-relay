import asyncio

from irc_relay.senders.irc import IrcClient
from irc_relay.messages.models import Message


class MessageReceiver:
    def send(self, message: Message) -> None:
        raise NotImplementedError


class IrcReceiver(MessageReceiver):
    def __init__(self, irc_client: IrcClient):
        self._irc_client = irc_client

    async def send(self, message: Message) -> None:
        await self._irc_client.send_to_channel(message.channel, message.string)


class DebugReceiver(MessageReceiver):
    async def send(self, message: Message) -> None:
        print(f"[{message.channel}] {message.string}")


class MessageDispatcher:
    def __init__(self):
        self._receivers = []

    def add_receiver(self, receiver: MessageReceiver):
        self._receivers.append(receiver)

    def remove_receiver(self, receiver: MessageReceiver):
        self._receivers.remove(receiver)

    async def send(self, message: Message) -> None:
        await asyncio.gather(*[receiver.send(message) for receiver in self._receivers])
