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
        self.prev_node = None

    def mark_node(self, node: JasonDebuggingTreeNode, result: Result):
        node.state = result

    def get_next(self) -> JasonDebuggingTreeNode:
        root = self.trees[0] # FIXME consider all trees later
        # diff = self.agent_repo.get_agent_state_diff(self.agent_name, root.im["start"], root.im["end"])
        # diff_groups = []
        # for key in ("B+", "B-"):
        #     diff_groups.append({
        #         "title" : key,
        #         "items" : diff[key]
        #     })
        # for key in ("G+", "G-"):
        #     ims = [str(im) for im in diff[key]]
        #     diff_groups.append({
        #         "title" : key,
        #         "items" : ims
        #     })
        self.prev_node = root
        # TODO handle navigation according to result of previous validation
        return root