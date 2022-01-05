class DebuggingTreeNode:
    def __init__(self, label, parent=None):
        self.label = label
        self.children = []
        self.parent = parent

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
        for child_im_id in im["children"]:
            child_im = agent_data["means"][child_im_id]
            node = JasonDebuggingTreeNode(agent_data, child_im)
            self.append_child(node)

    @staticmethod
    def create(agent_data, selected_plan):
        result = []
        for im_id in agent_data["means"]:
            im = agent_data["means"][im_id]
            if im["plan"] == selected_plan:
                result.append(JasonDebuggingTreeNode(agent_data, im))
        return result