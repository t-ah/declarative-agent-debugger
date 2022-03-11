from typing import Optional

from PyQt6.QtWidgets import QWidget, QGridLayout, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QTreeWidgetItem, \
    QTreeWidget, QAbstractItemView, QFormLayout
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt

from model.bdi import Intention
from model.agent import AgentData, AgentRepository
from debug.navigation_strategy import JasonDebuggingTreeNode, SimpleJasonNavigationStrategy, Result


class DebuggingScreen(QWidget):
    def __init__(self, app, selected_plan, selected_agent: str):
        super(DebuggingScreen, self).__init__()
        self.app = app
        self.agent_repo = self.app.agent_repo
        self.selected_agent = selected_agent
        self.agent_data = self.agent_repo.get_agent_data(selected_agent)
        self.grid = QGridLayout()
        self.setLayout(self.grid)
        self.node: Optional[JasonDebuggingTreeNode] = None
        self.question_view: Optional[QWidget] = None
        self.bug: Optional[Bug] = None

        trees = DebuggingScreen.create_trees(self.agent_data, selected_plan)
        if not trees:
            self.back()  # TODO show message
            return
        self.strategy = SimpleJasonNavigationStrategy(trees, self.agent_repo, selected_agent)

        self.tree_view = DebuggingTreeView(trees)
        self.grid.addWidget(self.tree_view, 0, 0)

        back_button = QPushButton("Back")
        self.grid.addWidget(back_button, 1, 0)
        back_button.clicked.connect(self.back)

        self.debug()

    @staticmethod
    def create_trees(agent_data: AgentData, selected_plan: str) -> list[JasonDebuggingTreeNode]:
        result = []
        for im in agent_data.intended_means.values():
            if im.plan.label == selected_plan:
                result.append(JasonDebuggingTreeNode(agent_data, im))
        return result

    def bug_located(self):
        result_view = ResultView()
        self.set_question_view(result_view)
        if self.bug:
            result_view.add_message(
                f"Bug located in {self.bug.file} line {self.bug.location}. Reason: {self.bug.reason}")

    def debug(self):
        next_node = self.strategy.get_next()
        if next_node:
            self.node = next_node
            self.tree_view.highlight_node(next_node)
            self.validate_goal_addition(next_node)
        else:
            buggy_node = self.strategy.final_bug
            if buggy_node:
                im = buggy_node.im
                self.bug = Bug(im.event.name if im.event else "", im.file, str(im.line))
            else:
                self.bug = Bug("No bug found", "-", "0")
            self.bug_located()

    def validate_goal_addition(self, node: JasonDebuggingTreeNode):
        im = node.im
        validation_widget = QWidget()
        self.set_question_view(validation_widget)
        validation_widget.setLayout(QFormLayout())
        validation_widget.setStyleSheet("QLabel {font: 16pt}")

        cause = f"Parent goal: {im.parent.trigger}" if im.parent else "Percept"
        if im.trigger[0] == "+":
            question = "Was it correct to add the goal?"
            self.bug = Bug(f"Bug in adding goal {im.trigger}.", "", "")
        else:
            question = "Is it 'acceptable' that the plan failed at this point?"
            self.bug = Bug(f"Plan for {im.trigger} should not have failed.", "", "")  # TODO show causing instr

        validation_widget.layout().addRow("Question", QLabel(question))
        validation_widget.layout().addRow("Goal (Trigger)", QLabel(im.trigger))
        validation_widget.layout().addRow("Cause", QLabel(cause))

        btn_bar = YesNoButtonBar()
        btn_bar.btn_yes.clicked.connect(lambda: self.goal_addition_validated(node))
        btn_bar.btn_no.clicked.connect(self.bug_located)
        validation_widget.layout().addRow(btn_bar)

        cycle = im.event.cycle if im.event else im.start

        validation_widget.layout().addRow(
            QLabel(f"State when goal added (cycle {str(cycle)}):"))

        state_view = AgentStateView(self.agent_repo, self.selected_agent, cycle)
        validation_widget.layout().addRow(state_view)

        self.set_question_view(validation_widget)

    def goal_addition_validated(self, node: JasonDebuggingTreeNode):
        self.validate_goal_result(node)

    def validate_goal_result(self, node: JasonDebuggingTreeNode):
        im = node.im
        validation_widget = QWidget()
        validation_widget.setLayout(QFormLayout())
        validation_widget.setStyleSheet("QLabel {font: 16pt}")

        validation_widget.layout().addRow("Question", QLabel("Has the goal been achieved?"))
        validation_widget.layout().addRow("Goal (Trigger)", QLabel(im.trigger))

        btn_bar = YesNoButtonBar()
        btn_bar.btn_yes.clicked.connect(self.goal_result_validated)
        btn_bar.btn_no.clicked.connect(self.goal_result_invalidated)
        validation_widget.layout().addRow(btn_bar)

        validation_widget.layout().addRow(QLabel(f"State after goal (cycle {im.end}):"))

        state_view = AgentStateView(self.agent_repo, self.selected_agent, im.end)
        validation_widget.layout().addRow(state_view)

        self.set_question_view(validation_widget)

    def goal_result_validated(self):
        self.strategy.mark_node(self.node, Result.Valid)
        self.tree_view.mark_validity(self.node, True)
        self.debug()

    def goal_result_invalidated(self):
        self.strategy.mark_node(self.node, Result.Invalid)
        self.tree_view.mark_validity(self.node, False)
        self.debug()

    def set_question_view(self, view: QWidget):
        if self.question_view:
            self.grid.removeWidget(self.question_view)
        self.question_view = view
        self.grid.addWidget(view, 0, 1)

    def back(self):
        self.app.show_plan_selection()


class YesNoButtonBar(QWidget):
    def __init__(self):
        super(YesNoButtonBar, self).__init__()
        self.setLayout(QHBoxLayout())
        self.btn_yes = QPushButton("Yes")
        self.btn_no = QPushButton("No")
        self.layout().addWidget(self.btn_yes)
        self.layout().addWidget(self.btn_no)


class DebuggingTreeView(QTreeWidget):
    def __init__(self, trees: list[JasonDebuggingTreeNode]):
        super(DebuggingTreeView, self).__init__()
        self.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.views = {}
        self.highlighted_node: Optional[JasonDebuggingTreeNode] = None
        self.color_std = QColor(0, 0, 0)
        self.color_highlight = QColor(0, 10, 100)
        self.color_valid = QColor(0, 150, 0)
        self.color_invalid = QColor(150, 0, 0)

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

    def color_node(self, node: JasonDebuggingTreeNode, color: QColor):
        view = self.views[node]
        if view:
            view.setBackground(0, color)

    def highlight_node(self, node: JasonDebuggingTreeNode):
        if self.highlighted_node:
            self.color_node(node, self.color_std)
        self.highlighted_node = node
        self.color_node(node, self.color_highlight)

    def mark_validity(self, node: JasonDebuggingTreeNode, valid: bool):
        self.color_node(node, self.color_valid if valid else self.color_invalid)


class AgentStateView(QWidget):
    def __init__(self, agent_repo: AgentRepository, agent_name: str, start_cycle=0, navigable=True):
        super(AgentStateView, self).__init__()
        self.agent_repo = agent_repo
        self.agent_name = agent_name
        self.agent_data = self.agent_repo.get_agent_data(self.agent_name)
        self.navigable = navigable
        self.start_cycle = start_cycle
        self.current_cycle = start_cycle

        self.setLayout(QVBoxLayout())

        self.belief_view = BeliefView()
        self.layout().addWidget(self.belief_view)
        self.intention_view = IntentionView(self.agent_data)
        self.layout().addWidget(self.intention_view)

        btn_prev = QPushButton("Prev")
        btn_next = QPushButton("Next")
        self.cycle_label = QLabel(str(start_cycle))  # TODO jump to cycle
        cycle_bar = QWidget()
        cycle_bar_layout = QHBoxLayout()
        cycle_bar.setLayout(cycle_bar_layout)
        cycle_bar_layout.addWidget(btn_prev)
        cycle_bar_layout.addWidget(self.cycle_label)
        cycle_bar_layout.addWidget(btn_next)
        btn_prev.clicked.connect(self.prev_cycle)
        btn_next.clicked.connect(self.next_cycle)
        self.layout().addWidget(cycle_bar)  # TODO reset button for jumping back to original cycle

        self.show_cycle(self.start_cycle)

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
        self.setLayout(QVBoxLayout())
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
    def __init__(self, agent_data: AgentData):
        super(IntentionView, self).__init__("Intentions")
        self.cycle = -1
        self.tree.setColumnWidth(0, 250)
        self.agent_data = agent_data
        self.tree.setHeaderLabels(["Event", "Trigger", "Context", "Result"])

    def set_intentions(self, intentions: list[Intention], cycle: int):
        self.tree.clear()
        self.cycle = cycle
        for intention in intentions:
            if not intention.means:
                continue
            root_im = intention.means[0]
            self.add_im_recursive(root_im, self.tree.invisibleRootItem())
        self.tree.expandAll()

    def add_im_recursive(self, im, parent_node: QTreeWidgetItem):
        if im.start > self.cycle:
            return
        res = im.res if im.end < self.cycle else ""
        node = QTreeWidgetItem([im.event.name if im.event else "", im.plan.trigger, im.plan.context, res])
        if im.end < self.cycle:
            node.setBackground(0, QColor(50, 50, 50))
        parent_node.addChild(node)
        for child_im in im.children:
            self.add_im_recursive(child_im, node)


class ResultView(QWidget):
    def __init__(self):
        super(ResultView, self).__init__()
        self.setLayout(QVBoxLayout())

    def add_message(self, msg):
        self.layout().addWidget(QLabel(msg))


class Bug:
    def __init__(self, reason: str, file: str, location: str):
        self.reason = reason
        self.file = file
        self.location = location

# class ValidationView(QWidget):
#     def __init__(self, controller: DebuggingScreen):
#         super(ValidationView, self).__init__()
#         self.controller = controller
#         layout = QVBoxLayout()
#         self.setLayout(layout)

#         self.item_list = QTreeWidget()
#         layout.addWidget(self.item_list)

#         button_bar = QWidget()
#         button_bar_layout = QHBoxLayout()
#         button_bar.setLayout(button_bar_layout)
#         layout.addWidget(button_bar)
#         btn_valid = QPushButton("Valid")
#         btn_invalid = QPushButton("Invalid")
#         btn_maybe = QPushButton("Unsure")
#         button_bar_layout.addWidget(btn_valid)
#         button_bar_layout.addWidget(btn_invalid)
#         button_bar_layout.addWidget(btn_maybe)

#     def present_node(self, node : JasonDebuggingTreeNode, item_groups: list[dict]) -> None:
#         self.node = node
#         self.item_list.clear()
#         root = self.item_list.invisibleRootItem()
#         for item_group in item_groups:
#             group_node = DebuggingTreeView.create_node(item_group["title"], color=(0, 10, 150))
#             root.addChild(group_node)
#             for item in item_group["items"]:
#                 custom_item = ValidationItem(item)
#                 list_item = QTreeWidgetItem(self.item_list)
#                 list_item.setSizeHint(0, custom_item.sizeHint())
#                 group_node.addChild(list_item)
#                 self.item_list.setItemWidget(list_item, 0, custom_item)


# class ValidationItem(QWidget):
#     def __init__(self, text: str):
#         super(ValidationItem, self).__init__()

#         self.checkbox = QCheckBox()
#         label = QLabel(text)
#         label.setWordWrap(True)

#         layout = QHBoxLayout()
#         self.setLayout(layout)
#         layout.addWidget(self.checkbox)
#         layout.addWidget(label, 1)
