from PyQt6.QtWidgets import QWidget, QGridLayout, QTreeView, QListView
from PyQt6.QtGui import QStandardItemModel, QStandardItem


class DebuggingScreen(QWidget):
    def __init__(self, app, selected_plan):
        super(DebuggingScreen, self).__init__()
        self.app = app
        self.agent_repo = self.app.agent_repo
        grid = QGridLayout()
        self.setLayout(grid)

        tree_view = DebuggingTreeView()
        grid.addWidget(tree_view, 0, 0)

        node_view = NodeView()
        grid.addWidget(node_view, 0, 1)


class DebuggingTreeView(QTreeView):
    def __init__(self):
        super(DebuggingTreeView, self).__init__()

        model = QStandardItemModel()
        parentItem = model.invisibleRootItem()
        for i in range(4):
            item = QStandardItem("item %d" % i)
            parentItem.appendRow(item)
            parentItem = item
        self.setModel(model)


class NodeView(QListView):
    def __init__(self):
        super(NodeView, self).__init__()

        model = QStandardItemModel()
        self.setModel(model)