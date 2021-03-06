from enum import Enum
from typing import Optional, Generator

from model.bdi import IntendedMeans
from model.agent import AgentRepository, AgentData


class Result(Enum):
    Undecided = 0
    Valid = 1
    Invalid = 2
    Skipped = 3


class JasonDebuggingTreeNode:
    def __init__(self, agent_data: AgentData, im: IntendedMeans):
        self.label = im.trigger
        self.children: list[JasonDebuggingTreeNode] = []
        self.parent: Optional[JasonDebuggingTreeNode] = None
        self.next_sibling: Optional[JasonDebuggingTreeNode] = None
        self.state = Result.Undecided
        self.im = im
        for child_im in im.children:
            child_node = JasonDebuggingTreeNode(agent_data, child_im)
            self.append_child(child_node)

    def append_child(self, node: "JasonDebuggingTreeNode"):
        if self.children:
            self.children[-1].next_sibling = node
        self.children.append(node)
        node.parent = self

    def traverse(self) -> Generator["JasonDebuggingTreeNode", None, None]:
        yield self
        for child in self.children:
            yield from child.traverse()


class SimpleJasonNavigationStrategy:
    def __init__(self, tree: JasonDebuggingTreeNode, agent_repo: AgentRepository, agent_name: str):
        self.tree = tree
        self.agent_repo = agent_repo
        for node in tree.traverse():
            node.state = Result.Undecided
        self.agent_name = agent_name
        self.prev_node: Optional[JasonDebuggingTreeNode] = None
        self.final_bug: Optional[JasonDebuggingTreeNode] = None

    @staticmethod
    def mark_node(node: JasonDebuggingTreeNode, result: Result):
        node.state = result

    def get_next(self):
        if not self.prev_node:
            self.prev_node = self.tree
            return self.tree

        node = self.prev_node
        if node.state == Result.Invalid:
            if node.children:
                self.prev_node = node.children[0]
                return self.prev_node
            else:
                self.final_bug = node
                return None
        elif node.state == Result.Valid:
            if node.next_sibling:
                self.prev_node = node.next_sibling
                return self.prev_node
            else:
                if node.parent and node.parent.state == Result.Invalid:
                    self.final_bug = node.parent
                return None
        return None
