from PyQt6.QtWidgets import QPushButton, QWidget, QGridLayout, QTreeView, QListView
from PyQt6.QtGui import QStandardItemModel, QStandardItem


class DebuggingScreen(QWidget):
    def __init__(self, app, selected_plan, selected_agent):
        super(DebuggingScreen, self).__init__()
        self.app = app
        self.agent_repo = self.app.agent_repo
        grid = QGridLayout()
        self.setLayout(grid)

        tree_view = DebuggingTreeView(selected_plan, selected_agent, app.agent_repo)
        grid.addWidget(tree_view, 0, 0)

        node_view = NodeView()
        grid.addWidget(node_view, 0, 1)

        back_button = QPushButton("Back")
        grid.addWidget(back_button, 1, 0)
        back_button.clicked.connect(self.navigate_back)

        # TODO select first item and begin navigation strategy

    def navigate_back(self):
        self.app.show_plan_selection()


class DebuggingTreeView(QTreeView):
    def __init__(self, selected_plan, selected_agent, agent_repo):
        super(DebuggingTreeView, self).__init__()
        self.selected_plan = selected_plan
        self.agent_data = agent_repo.get(selected_agent)

        model = QStandardItemModel()
        self.setModel(model)

        root = model.invisibleRootItem()
        for im_id in self.agent_data["means"]:
            im = self.agent_data["means"][im_id]
            if im["plan"] == selected_plan:
                self.add_im_node(root, im)

    def add_im_node(self, parent_node, im):
        item = QStandardItem(self.agent_data["plans"][im["plan"]]["trigger"] +" "+ str(im["intention"]))
        parent_node.appendRow(item)
        for child_im_id in im["children"]:
            child_im = self.agent_data["means"][child_im_id]
            self.add_im_node(item, child_im)


class NodeView(QListView):
    def __init__(self):
        super(NodeView, self).__init__()

        model = QStandardItemModel()
        self.setModel(model)