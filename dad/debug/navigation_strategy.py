from typing import Optional

from model.agent import AgentRepository
from debug.tree import DebuggingTreeNode, JasonDebuggingTreeNode, Result



class AbstractNavigationStrategy:
    def __init__(self, trees: list[DebuggingTreeNode], agent_repo: AgentRepository):
        ...

    def get_next(self) -> DebuggingTreeNode:
        """Get the next node to be validated."""
        ...

    def mark_node(self, node: DebuggingTreeNode, result: Result):
        """Mark any node as in/valid or skipped."""
        ...

    def get_result(self) -> object:
        ...


class SimpleJasonNavigationStrategy:
    def __init__(self, trees: list[JasonDebuggingTreeNode], agent_repo: AgentRepository, agent_name: str):
        self.trees = trees
        self.agent_repo = agent_repo
        for tree in self.trees:
            for node in tree.traverse():
                node.state = Result.Undecided
        self.agent_name = agent_name
        self.prev_node: JasonDebuggingTreeNode
        self.final_bug: JasonDebuggingTreeNode

    def mark_node(self, node: JasonDebuggingTreeNode, result: Result):
        node.state = result

    def get_next(self):
        if not self.prev_node:
            root = self.trees[0] # FIXME consider all trees later
            self.prev_node = root
            return root

        node = self.prev_node
        if node.state == Result.Invalid:
            if node.children:
                return node.children[0]
            else:
                self.final_bug = node
                return None
        elif node.state == Result.Valid:
            if node.next_sibling:
                return node.next_sibling
            else:
                if node.parent and node.parent.state == Result.Invalid:
                    self.final_bug = node.parent
                return None
        return None
