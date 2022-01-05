from enum import Enum

from debug.tree import DebuggingTreeNode, JasonDebuggingTreeNode


class Result(Enum):
    Undecided = 0
    Valid = 1
    Invalid = 2
    Skipped = 3


class AbstractNavigationStrategy:
    def __init__(self, trees: list[DebuggingTreeNode]):
        self.trees = trees
        for tree in self.trees:
            for node in tree.traverse():
                node.state = Result.Undecided

    def get_next_node(self) -> DebuggingTreeNode:
        """Get the next node to be validated."""
        ...

    def mark_node(self, node: DebuggingTreeNode, result: Result):
        """Mark any node as in/valid or skipped."""
        ...

    def has_next(self) -> bool:
        ...


class SimpleJasonNavigationStrategy(AbstractNavigationStrategy):
    def __init__(self, trees: list[JasonDebuggingTreeNode]):
        super().__init__(trees)

    def mark_node(self, node: DebuggingTreeNode, result: Result):
        node.state = result