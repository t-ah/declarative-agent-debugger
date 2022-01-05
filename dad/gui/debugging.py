from PyQt6.QtWidgets import QPushButton, QWidget, QGridLayout, QTreeView, QListView
from PyQt6.QtGui import QColor, QStandardItemModel, QStandardItem

from debug.tree import DebuggingTreeNode, JasonDebuggingTreeNode
from debug.navigation_strategy import SimpleJasonNavigationStrategy


class DebuggingScreen(QWidget):
    def __init__(self, app, selected_plan, selected_agent):
        super(DebuggingScreen, self).__init__()
        self.app = app
        self.agent_repo = self.app.agent_repo
        self.agent_data = self.agent_repo.get_agent_data(selected_agent)
        grid = QGridLayout()
        self.setLayout(grid)

        trees = JasonDebuggingTreeNode.create(self.agent_data, selected_plan)
        strategy = SimpleJasonNavigationStrategy(trees) # TODO allow selection of nav-strategy

        tree_view = DebuggingTreeView(trees)
        grid.addWidget(tree_view, 0, 0)

        node_view = ValidationView()
        grid.addWidget(node_view, 0, 1)

        back_button = QPushButton("Back")
        grid.addWidget(back_button, 1, 0)
        back_button.clicked.connect(self.back)

        while strategy.has_next():
            node = strategy.get_next_node()
            # TODO

    def back(self):
        self.app.show_plan_selection()


class DebuggingTreeView(QTreeView):
    def __init__(self, trees: list[DebuggingTreeNode]):
        super(DebuggingTreeView, self).__init__()

        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(["Debugging Tree"])
        self.setModel(model)

        for tree in trees:
            for node in tree.traverse():
                node.view = DebuggingTreeView.create_node(node.label)
                parent_view = node.parent.view if node.parent else model.invisibleRootItem()
                parent_view.appendRow(node.view)

        self.expandRecursively(model.invisibleRootItem().index())

    @staticmethod
    def create_node(label) -> QStandardItem:
        item = QStandardItem(label)
        item.setEditable(False)
        item.setBackground(QColor(0, 0, 100))
        return item


class ValidationView(QListView):
    def __init__(self):
        super(ValidationView, self).__init__()

        model = QStandardItemModel()
        self.setModel(model)