import dataclasses


@dataclasses.dataclass
class Message:
    string: str
    channel: str

    def __str__(self) -> str:
        return f"Message<{self.channel}>({self.string})"
