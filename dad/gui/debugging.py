from select import select
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from dad.debug.tree import Result

from model.agent import AgentRepository
from debug.tree import DebuggingTreeNode, JasonDebuggingTreeNode
from debug.navigation_strategy import SimpleJasonNavigationStrategy


class DebuggingScreen(QWidget):
    def __init__(self, app, selected_plan, selected_agent: str):
        super(DebuggingScreen, self).__init__()
        self.app = app
        self.agent_repo = self.app.agent_repo
        self.selected_agent = selected_agent
        self.agent_data = self.agent_repo.get_agent_data(selected_agent)
        self.grid = QGridLayout()
        self.setLayout(self.grid)
        self.current_node: JasonDebuggingTreeNode
        self.question_view: QWidget

        trees = DebuggingScreen.create_trees(self.agent_data, selected_plan)
        self.strategy = SimpleJasonNavigationStrategy(trees, self.agent_repo, selected_agent) # TODO allow selection of nav-strategy

        tree_view = DebuggingTreeView(trees)
        self.grid.addWidget(tree_view, 0, 0)

        back_button = QPushButton("Back")
        self.grid.addWidget(back_button, 1, 0)
        back_button.clicked.connect(self.back)

        self.debug()

    @staticmethod
    def create_trees(agent_data, selected_plan) -> list[JasonDebuggingTreeNode]:
        result = []
        for im_id in agent_data["means"]:
            im = agent_data["means"][im_id]
            if im["plan"] == selected_plan:
                result.append(JasonDebuggingTreeNode(agent_data, im))
        return result

    def bug_located(self):
        pass # TODO

    def debug(self):
        # TODO highlight current node
        self.node = self.strategy.get_next() # TODO continue debugging until done
        self.validate_goal_addition()

    def validate_goal_addition(self):
        im = self.node.im
        validation_widget = QWidget()
        self.question_view = validation_widget
        validation_widget.setLayout(QVBoxLayout())

        event = im["event"]["name"]
        instruction = im["event"]["instruction"]
        question = "Are goal instantiation and context correct?" if event[0] == "+" else "Is it 'acceptable' that the plan failed at this point?"
        validation_widget.layout().addWidget(QLabel(question))
        validation_widget.layout().addWidget(QLabel(f"Goal (Event): {event}"))
        validation_widget.layout().addWidget(QLabel(f"Previous instruction: {instruction}"))

        state_view = AgentStateView(self.agent_repo, self.selected_agent, im["event"]["cycle"])
        validation_widget.layout().addWidget(state_view)

        btn_bar = QWidget()
        btn_bar.setLayout(QHBoxLayout())
        btn_yes = QPushButton("Yes")
        btn_yes.clicked.connect(self.goal_addition_validated)
        btn_no = QPushButton("No")
        btn_no.clicked.connect(self.bug_located)
        for widget in [btn_yes, btn_no]:
            btn_bar.layout().addWidget(widget)
        validation_widget.layout().addWidget(btn_bar)

        self.set_question_view(validation_widget)

    def goal_addition_validated(self):
        self.validate_goal_result()

    def validate_goal_result(self):
        im = self.node.im
        validation_widget = QWidget()
        validation_widget.setLayout(QVBoxLayout())

        validation_widget.layout().addWidget(QLabel("Has the goal been achieved?"))
        validation_widget.layout().addWidget(QLabel(f"Goal (Event): {im['event']['name']}"))

        state_view = AgentStateView(self.agent_repo, self.selected_agent, im["end"])
        validation_widget.layout().addWidget(state_view)

        btn_bar = QWidget()
        btn_bar.setLayout(QHBoxLayout())
        btn_yes = QPushButton("Yes")
        btn_yes.clicked.connect(self.goal_result_validated)
        btn_no = QPushButton("No")
        btn_no.clicked.connect(self.goal_result_invalidated)
        for widget in [btn_yes, btn_no]:
            btn_bar.layout().addWidget(widget)
        validation_widget.layout().addWidget(btn_bar)

        self.set_question_view(validation_widget)

    def goal_result_validated(self):
        self.strategy.mark_node(self.node, Result.Valid)
        self.debug()

    def goal_result_invalidated(self):
        self.strategy.mark_node(self.node, Result.Invalid)
        self.debug()

    def set_question_view(self, view: QWidget):
        if self.question_view:
            self.grid.removeWidget(self.question_view)
        self.question_view = view
        self.grid.addWidget(view, 0, 1)

    def back(self):
        self.app.show_plan_selection()


class DebuggingTreeView(QTreeWidget):
    def __init__(self, trees: list[JasonDebuggingTreeNode]):
        super(DebuggingTreeView, self).__init__()
        self.views = {}

        for tree in trees:
            for node in tree.traverse():
                node_view = DebuggingTreeView.create_node(node.label)
                self.views[node] = node_view
                parent_view = self.views[node.parent] if node.parent else self.invisibleRootItem()
                parent_view.addChild(node_view)

        self.expandAll()

    @staticmethod
    def create_node(label, color=None) -> QTreeWidgetItem:
        item = QTreeWidgetItem()
        item.setText(0, label)
        if color:
            item.setBackground(0, QColor(*color))
        return item


class AgentStateView(QWidget):
    def __init__(self, agent_repo: AgentRepository, agent_name: str, start_cycle=0, navigable=True):
        super(AgentStateView, self).__init__()
        self.agent_repo = agent_repo
        self.agent_name = agent_name
        self.agent_data = self.agent_repo.get_agent_data(self.agent_name)
        self.navigable = navigable
        self.start_cycle = start_cycle
        self.current_cycle = start_cycle

        btn_prev = QPushButton("Prev")
        btn_next = QPushButton("Next")
        self.cycle_label = QLabel(str(start_cycle)) # TODO jump to cycle
        cycle_bar = QWidget()
        cycle_bar_layout = QHBoxLayout()
        cycle_bar.setLayout(cycle_bar_layout)
        cycle_bar_layout.addWidget(btn_prev)
        cycle_bar_layout.addWidget(self.cycle_label)
        cycle_bar_layout.addWidget(btn_next)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(cycle_bar) # TODO reset button for jumping back to original cycle

        self.belief_view = BeliefView()
        self.layout().addWidget(self.belief_view)
        self.intention_view = IntentionView(self.agent_data)
        self.layout().addWidget(self.intention_view)

        self.show_cycle(self.start_cycle)

        btn_prev.clicked.connect(self.prev_cycle)
        btn_next.clicked.connect(self.next_cycle)

    def show_cycle(self, cycle):
        self.current_cycle = cycle
        self.cycle_label.setText(str(cycle))
        state = self.agent_repo.get_agent_state(self.agent_name, self.current_cycle)
        self.belief_view.set_beliefs(state["beliefs"])
        self.intention_view.set_intentions(state["intentions"], cycle)

    def prev_cycle(self):
        if self.current_cycle > 0:
            self.show_cycle(self.current_cycle - 1)

    def next_cycle(self):
        self.show_cycle(self.current_cycle + 1)


class TreeView(QWidget):
    def __init__(self, title):
        super(TreeView, self).__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.tree = QTreeWidget()
        self.layout().addWidget(QLabel(title))
        self.layout().addWidget(self.tree)


class BeliefView(TreeView):
    def __init__(self):
        super(BeliefView, self).__init__("Beliefs")
        self.tree.setColumnWidth(0, 1000)
        self.tree.setHeaderLabels(["Belief"])

    def set_beliefs(self, beliefs: list[str]):
        self.tree.clear()
        for belief in beliefs:
            self.tree.addTopLevelItem(QTreeWidgetItem([belief]))


class IntentionView(TreeView):
    def __init__(self, agent_data):
        super(IntentionView, self).__init__("Intentions")
        self.tree.setColumnWidth(0, 250)
        self.agent_data = agent_data
        self.tree.setHeaderLabels(["Event", "Trigger", "Context", "Result"])

    def set_intentions(self, intentions: list, cycle: int):
        self.tree.clear()
        self.cycle = cycle
        for intention in intentions:
            if not intention["means"]:
                continue
            root_im = intention["means"][0]
            self.add_im_recursive(root_im, self.tree.invisibleRootItem())
        self.tree.expandAll()

    def add_im_recursive(self, im_id, parent_node: QTreeWidgetItem):
        im = self.agent_data["means"][im_id]
        if im["start"] > self.cycle:
            return
        plan = self.agent_data["plans"][im["plan"]]
        res = im["res"] if im["end"] < self.cycle else ""
        node = QTreeWidgetItem([im["event"]["name"], plan["trigger"], plan.get("ctx", "T"), res])
        if im["end"] < self.cycle:
            node.setBackground(0, QColor(50,50,50))
        parent_node.addChild(node)
        for child_im in im["children"]:
            self.add_im_recursive(child_im, node)


class ValidationView(QWidget):
    def __init__(self, controller: DebuggingScreen):
        super(ValidationView, self).__init__()
        self.controller = controller
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.item_list = QTreeWidget()
        layout.addWidget(self.item_list)

        button_bar = QWidget()
        button_bar_layout = QHBoxLayout()
        button_bar.setLayout(button_bar_layout)
        layout.addWidget(button_bar)
        btn_valid = QPushButton("Valid")
        btn_invalid = QPushButton("Invalid")
        btn_maybe = QPushButton("Unsure")
        button_bar_layout.addWidget(btn_valid)
        button_bar_layout.addWidget(btn_invalid)
        button_bar_layout.addWidget(btn_maybe)

    def present_node(self, node : DebuggingTreeNode, item_groups: list[dict]) -> None:
        self.node = node
        self.item_list.clear()
        root = self.item_list.invisibleRootItem()
        for item_group in item_groups:
            group_node = DebuggingTreeView.create_node(item_group["title"], color=(0, 10, 150))
            root.addChild(group_node)
            for item in item_group["items"]:
                custom_item = ValidationItem(item)
                list_item = QTreeWidgetItem(self.item_list)
                list_item.setSizeHint(0, custom_item.sizeHint())
                group_node.addChild(list_item)
                self.item_list.setItemWidget(list_item, 0, custom_item)


class ValidationItem(QWidget):
    def __init__(self, text: str):
        super(ValidationItem, self).__init__()

        self.checkbox = QCheckBox()
        label = QLabel(text)
        label.setWordWrap(True)

        layout = QHBoxLayout()
        self.setLayout(layout)
        layout.addWidget(self.checkbox)
        layout.addWidget(label, 1)