import logging
from typing import List, Optional, Tuple

from irc_relay.messages.models import Message, ProcessedEdit

logger = logging.getLogger(__name__)


class StringHuggleMessageProcessor:
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

        messages = []
        if message.string.endswith("# Reverted"):
            messages.append(("#en.wikipedia.huggle", f"ROLLBACK {diff_id}"))
        elif score and score > 0.1:
            huggle_score = int((score - 0.2) * 1000)
            messages.append(("#en.wikipedia.huggle", f"SCORED {diff_id} {huggle_score}"))
        return messages


class RevertMessageProcessor:
    def _format_revert_message(self, edit: ProcessedEdit) -> str:
        score_str = f"{edit.score:.6f}" if edit.score is not None else ""
        return (
            f"\x0315[[\x0307{edit.change.title}\x0315]] by \"\x0303{edit.change.user}\x0315\""
            f" (\x0312 {edit.change.url} \x0315) \x0306{score_str}\x0315"
            f" (\x0304Reverted\x0315) (\x0313{edit.comment or ''}\x0315)"
        )


class HuggleMessageProcessor:
    def _format_huggle_message(self, revision_id: int, score: Optional[float], reverted: bool) -> Optional[str]:
        if reverted:
            return f"ROLLBACK {revision_id}"
        if score is not None and score > 0.1:
            return f"SCORED {revision_id} {int((score - 0.2) * 1000)}"
        return None


class ClueBotNGMessageProcessor(RevertMessageProcessor, HuggleMessageProcessor):
    def _get_edit_messages(
        self,
        edit: ProcessedEdit,
        revert_channel: Optional[str],
        huggle_channel: Optional[str],
    ) -> list[tuple[str, str]]:
        messages = []

        if revert_channel and edit.reverted:
            messages.append((revert_channel, self._format_revert_message(edit)))

        if huggle_channel:
            if text := self._format_huggle_message(edit.change.revision_id, edit.score, edit.reverted):
                messages.append((huggle_channel, text))

        return messages
