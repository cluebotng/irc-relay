import dataclasses


@dataclasses.dataclass
class TextMessage:
    string: str
    channel: str


@dataclasses.dataclass
class EditChange:
    title: str
    user: str
    url: str
    revision_id: int
    namespace: str = ""
    flags: list[str] = dataclasses.field(default_factory=list)
    length: str | None = None
    comment: str = ""


@dataclasses.dataclass
class ProcessedEdit:
    change: EditChange
    reverted: bool
    comment: str | None
    score: float | None


@dataclasses.dataclass
class WarnedUser:
    username: str
    level: int
