import logging
from typing import List, Tuple

from irc_relay.messages.models import Message

logger = logging.getLogger(__name__)


class HuggleMessageProcessor:
    async def _get_huggle_messages(self, message: Message) -> List[Tuple[str, str]]:
        # Convert ClueBot NG formatted messages into Huggle formatted messages
        # x-ref https://github.com/huggle/cluenet-relay/blob/master/CluebotRelay/cluebotrelay.cpp#L69
        if message.channel != "#wikipedia-en-cbngfeed":
            logger.debug(f"Ignoring non-feed message: {message}")
            return []

        if "diff=" not in message.string:
            logger.debug(f"Ignoring message with no diff {message}")
            return []

        diff_id = message.string.split("diff=")[1].split("&")[0]
        if not diff_id:
            logger.warning(f"Failed to parse diff id from {message}")
            return []

        score = None
        if "# Whitelisted" not in message.string:
            parts = message.string.split("#")
            if len(parts) > 3:
                # At the end of the message we expect something like
                # `# 0.000000 # Below threshold # Not reverted`
                # The score is in the first 'comment' so grab it
                try:
                    score = float(parts[-3].strip())
                except ValueError:
                    logger.error(f"Parsed score is not a number: {parts}")

        messages = [("#en.wikipedia.huggle", f"ROLLBACK {diff_id}")]
        if score and score > 0.1:
            huggle_score = int((score - 0.2) * 1000)
            messages.append(("#en.wikipedia.huggle", f"SCORED {diff_id} {huggle_score}"))
        return messages
