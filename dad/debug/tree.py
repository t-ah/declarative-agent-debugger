from enum import Enum


class Result(Enum):
    Undecided = 0
    Valid = 1
    Invalid = 2
    Skipped = 3


class DebuggingTreeNode:
    def __init__(self, label, parent=None):
        self.label = label
        self.children = []
        self.parent = parent
        self.state = Result.Undecided

    def append_child(self, node):
        self.children.append(node)
        node.parent = self

    def traverse(self):
        yield self
        for child in self.children:
            yield from child.traverse()


class JasonDebuggingTreeNode(DebuggingTreeNode):
    def __init__(self, agent_data, im):
        super().__init__(agent_data["plans"][im["plan"]]["trigger"] +" id="+ str(im["intention"]))
        self.im = im
        for child_im_id in im["children"]:
            child_im = agent_data["means"][child_im_id]
            node = JasonDebuggingTreeNode(agent_data, child_im)
            self.append_child(node)