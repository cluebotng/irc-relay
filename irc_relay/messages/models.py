import dataclasses
from typing import Optional


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
    length: Optional[int] = None
    comment: str = ""


@dataclasses.dataclass
class ProcessedEdit:
    change: EditChange
    reverted: bool
    comment: Optional[str]
    score: Optional[float]
