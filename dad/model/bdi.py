from dataclasses import dataclass
from typing import Optional
from enum import Enum


class EventType(Enum):
    BELIEF_UPDATE = 1
    SUB_GOAL = 2
    GOAL_NEW_FOCUS = 3


@dataclass
class BDIEvent:
    id:             int
    parent:         Optional["IntendedMeans"]
    name:           str
    type:           EventType
    cycle_added:    int
    cycle_selected: int

    def is_goal(self) -> bool:
        return self.type != EventType.BELIEF_UPDATE


@dataclass
class FailureReason:
    msg: str
    type: str
    src: str
    line: int

    @staticmethod
    def from_jason_dict(d: dict) -> "FailureReason":
        return FailureReason(d["error_msg"], f'{d["error"]} / {d["type"]}', d["code_src"], d["code_line"])


@dataclass
class IntendedMeans:
    id:             int
    intention:      "Intention"
    start:          int
    end:            int
    res:            str
    failure_reason: Optional[FailureReason]
    file:           str
    line:           int
    instructions:   list["Instruction"]
    plan:           "Plan"
    trigger:        str
    context:        str
    children:       list["IntendedMeans"]
    parent:         Optional["IntendedMeans"]
    event:          Optional[BDIEvent]

    def get_event_name(self) -> str:
        return self.event.name if self.event else ""

    def get_event_added(self) -> str:
        return str(self.event.cycle_added) if self.event else ""


@dataclass
class Intention:
    id:     int
    start:  int
    end:    int
    means:  list[IntendedMeans]
    events: list[BDIEvent]


@dataclass
class BeliefChange:
    cycle:  int
    added:  bool
    belief: str


@dataclass
class Plan:
    label:      str
    trigger:    str
    context:    str
    body:       str
    file:       str
    line:       int
    used:       int = 0

    def readable(self) -> str:
        f_body = ";\n".join(["\t" + x for x in self.body.split("; ")])
        return f"{self.trigger} : {self.context} <-\n{f_body}."


@dataclass
class Instruction:
    file: str
    line: int
    text: str
    unifier: str = "{}"

    def __str__(self):
        return f"{self.text} : {self.unifier}"
