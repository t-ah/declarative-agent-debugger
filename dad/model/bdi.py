from dataclasses import dataclass
from typing import Optional


@dataclass
class BDIEvent:
    parent: Optional["IntendedMeans"]
    cycle: int
    name: str
    selected: int


@dataclass
class IntendedMeans:
    id: int
    intention: "Intention"
    start: int
    end: int
    res: str
    file: str
    line: int
    plan: "Plan"
    trigger: str
    children: list["IntendedMeans"]
    parent: Optional["IntendedMeans"]
    event: Optional[BDIEvent]

    def get_event_name(self) -> str:
        return self.event.name if self.event else ""


@dataclass
class Intention:
    id: int
    start: int
    end: int
    means: list[IntendedMeans]
    instructions: list[str]
    events: list[BDIEvent]


@dataclass
class BeliefChange:
    cycle: int
    added: bool
    belief: str


@dataclass
class Plan:
    label: str
    trigger: str
    context: str
    body: str
    file: str
    line: int
    used: int = 0
