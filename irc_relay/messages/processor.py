from irc_relay.messages.models import ProcessedEdit, WarnedUser


class RevertMessageProcessor:
    def _format_revert_message(self, edit: ProcessedEdit) -> str:
        score_str = f"{edit.score:.6f}" if edit.score is not None else ""
        return (
            f'\x0315[[\x0307{edit.change.title}\x0315]] by "\x0303{edit.change.user}\x0315"'
            f" (\x0312 {edit.change.url} \x0315) \x0306{score_str}\x0315"
            f" (\x0304Reverted\x0315) (\x0313{edit.comment or ''}\x0315)"
        )


class WarnMessageProcessor:
    def _format_huggle_warn_message(self, warn: WarnedUser) -> str:
        return f"WARN {warn.level} {warn.username}"


class HuggleMessageProcessor:
    def _format_huggle_message(self, revision_id: int, score: float | None, reverted: bool) -> str | None:
        if reverted:
            return f"ROLLBACK {revision_id}"
        if score is not None and score > 0.1:
            return f"SCORED {revision_id} {int((score - 0.2) * 1000)}"
        return None


class ClueBotNGMessageProcessor(RevertMessageProcessor, HuggleMessageProcessor, WarnMessageProcessor):
    def _get_edit_messages(
        self,
        edit: ProcessedEdit,
        revert_channel: str | None,
        huggle_channel: str | None,
    ) -> list[tuple[str, str]]:
        messages = []

        if revert_channel and edit.reverted:
            messages.append((revert_channel, self._format_revert_message(edit)))

        if huggle_channel:
            if text := self._format_huggle_message(edit.change.revision_id, edit.score, edit.reverted):
                messages.append((huggle_channel, text))

        return messages

    def _get_warn_messages(
        self,
        warn: WarnedUser,
        huggle_channel: str | None,
    ) -> list[tuple[str, str]]:
        messages = []

        if huggle_channel:
            messages.append((huggle_channel, self._format_huggle_warn_message(warn)))

        return messages
