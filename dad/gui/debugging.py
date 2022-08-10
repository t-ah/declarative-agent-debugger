from typing import Optional, Callable

from PyQt6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QTreeWidgetItem, \
    QTreeWidget, QAbstractItemView, QFormLayout, QSplitter, QComboBox
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt

from model.bdi import Intention, Instruction, IntendedMeans, InstructionType
from model.agent import AgentData, AgentRepository
from debug.navigation_strategy import JasonDebuggingTreeNode, SimpleJasonNavigationStrategy, Result


class DebuggingScreen(QWidget):
    def __init__(self, app, selected_goal: int, selected_agent: str):
        super(DebuggingScreen, self).__init__()
        self.app = app
        self.agent_repo: AgentRepository = self.app.agent_repo
        self.selected_agent: str = selected_agent
        self.agent_data: AgentData = self.agent_repo.get_agent_data(selected_agent)
        self.node: Optional[JasonDebuggingTreeNode] = None
        self.question_view: Optional[QWidget] = None
        self.bug: Optional[Bug] = None
        self.instruction_views: dict[Instruction, QTreeWidgetItem] = {}

        QHBoxLayout(self)
        self.splitter = QSplitter()
        tree_pane = QWidget(self.splitter)
        QVBoxLayout(tree_pane)
        self.question_view_container = QWidget(self.splitter)
        QHBoxLayout(self.question_view_container)
        self.layout().addWidget(self.splitter)

        tree = DebuggingScreen.create_tree(self.agent_data, selected_goal)
        self.strategy = SimpleJasonNavigationStrategy(tree, self.agent_repo, selected_agent)

        self.tree_view = DebuggingTreeView(tree)
        tree_pane.layout().addWidget(self.tree_view)

        button_bar = QWidget()
        tree_pane.layout().addWidget(button_bar)
        back_button = QPushButton("Back", button_bar)
        QHBoxLayout(button_bar)
        button_bar.layout().addStretch()
        back_button.clicked.connect(self.back)

        self.debug()

    @staticmethod
    def create_tree(agent_data: AgentData, selected_im: int) -> JasonDebuggingTreeNode:
        return JasonDebuggingTreeNode(agent_data, agent_data.intended_means.get(selected_im))

    def buggy_goal_located(self):
        result_view = FormWidget()
        self.set_question_view(result_view)
        if self.bug:
            result_view.add_row(
                f"Bug located in\n{self.bug.file}\nline {self.bug.location}.\nReason: {self.bug.reason}")
            result_view.add_row(f"Code:\n{self.bug.code}")
            cont_button = QPushButton("Debug goal/plan")
            result_view.add_button(cont_button)
            cont_button.clicked.connect(lambda: self.debug_plan(self.strategy.final_bug.im, 0))
        else:
            result_view.add_row("Sorry, no bug could be located.")

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
                self.bug = Bug(im.event.name if im.event else "", im.file, str(im.line), code=im.plan.readable())
                self.instruction_views = self.tree_view.expand_node_with_plan_instructions(buggy_node)
            else:
                self.bug = None
            self.buggy_goal_located()

    def debug_plan(self, im: IntendedMeans, instruction_index: int):
        if instruction_index >= len(im.instructions):
            self.buggy_goal_but_no_instruction_found(im)
            return
        instruction = im.instructions[instruction_index]
        if instruction.text.startswith("!"):
            self.tree_view.mark_view(self.instruction_views[instruction], True)
            self.debug_plan(im, instruction_index + 1)
        else:
            instruction_type = instruction.get_type()
            self.tree_view.highlight_view(self.instruction_views[instruction])
            instruction_widget = FormWidget()
            self.set_question_view(instruction_widget)
            instruction_widget.add_row("Question", "Did the instruction produce the expected results?")
            instruction_widget.add_row("Instruction", str(instruction))
            instruction_widget.add_row("Type", str(instruction_type.value))
            # TODO: show result information depending on instruction type
            if instruction_type == InstructionType.MENTAL_NOTE:
                cycle = instruction.cycle
                diff = self.agent_repo.get_cycle_diff(self.selected_agent, cycle)
                instruction_widget.add_row("Beliefs added:")
                instruction_widget.layout().addRow(BeliefView(diff.beliefs_added))
                instruction_widget.add_row("Beliefs deleted:")
                instruction_widget.layout().addRow(BeliefView(diff.beliefs_deleted))
            elif instruction_type == InstructionType.ACTION:
                # TODO
                pass  # ???
            elif instruction_type == InstructionType.INTERNAL_ACTION:
                pass
            elif instruction_type == InstructionType.TEST_GOAL:
                pass
            elif instruction_type == InstructionType.EXPRESSION:
                pass
            else:
                instruction_widget.add_row(f"Instruction type {instruction_type.value} not supported")
            instruction_widget.add_yes_no_buttons(lambda: self.debug_plan(im, instruction_index + 1),
                                                  lambda: self.buggy_instruction_found(im, instruction_index))

    def validate_goal_addition(self, node: JasonDebuggingTreeNode):
        im = node.im
        validation_widget = FormWidget()
        self.set_question_view(validation_widget)

        cause = f"Parent goal: {im.parent.trigger}" if im.parent else "Percept"
        if im.trigger[0] == "+":
            question = "Was it correct to add the goal?"
            self.bug = Bug(f"Bug in adding goal {im.trigger}.", "", "")
        else:
            question = "Is it 'acceptable' that the plan failed at this point?"
            self.bug = Bug(f"Plan for {im.trigger} should not have failed.", "", "")

        validation_widget.add_row("Question", question)
        validation_widget.add_row("Goal (Trigger)", im.trigger)
        validation_widget.add_row("Origin", cause)
        validation_widget.add_yes_no_buttons(lambda: self.goal_addition_validated(node), self.buggy_goal_located)

        cycle = im.event.cycle_added if im.event else im.start
        validation_widget.add_row("Agent state")

        state_view = AgentStateView(self.agent_repo, self.selected_agent, cycle, "Goal added")
        validation_widget.layout().addRow(state_view)

        self.set_question_view(validation_widget)

    def goal_addition_validated(self, node: JasonDebuggingTreeNode):
        self.validate_goal_result(node)

    def validate_goal_result(self, node: JasonDebuggingTreeNode):
        im = node.im
        validation_widget = FormWidget()

        validation_widget.add_row("Goal", im.trigger)

        if im.res == "np":
            validation_widget.add_row("Question", "Is an applicable plan missing?")
        elif im.res == "failed":
            reason = im.failure_reason
            validation_widget.add_row("Failure:", reason.type)
            validation_widget.add_row("Failure message:", reason.msg)
            validation_widget.add_row("Failure location:", f"{reason.src}:{reason.line}")
            validation_widget.add_row("", "")
            validation_widget.add_row("Question", "Is this goal failure acceptable?")
        else:  # im.res == "achieved", belief trigger, etc.
            validation_widget.add_row("Question", "Has the goal been achieved?")
        validation_widget.add_row("", "")
        validation_widget.add_yes_no_buttons(self.goal_result_validated, self.goal_result_invalidated)
        validation_widget.layout().addRow(QLabel(f"State"))

        state_view = AgentStateView(self.agent_repo, self.selected_agent, im.end, "Goal finished")
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

    def buggy_instruction_found(self, im: IntendedMeans, instruction_index: int):
        buggy_instruction = im.instructions[instruction_index]
        result_view = FormWidget()
        result_view.add_row("Buggy instruction located:")
        result_view.add_row("Instruction:", str(buggy_instruction))
        result_view.add_row("File:", buggy_instruction.file)
        result_view.add_row("Line:", str(buggy_instruction.line))
        result_view.add_row("In goal:", im.get_event_name())
        self.set_question_view(result_view)

    def buggy_goal_but_no_instruction_found(self, im: IntendedMeans):
        result_view = FormWidget()
        result_view.add_row("Buggy goal located:")
        result_view.add_row(im.get_event_name())
        result_view.add_row("File:", im.file)
        result_view.add_row("Line:", str(im.line))
        result_view.add_row("No buggy instruction could be determined:")
        result_view.add_row("1. Consider if any instruction is missing.")
        result_view.add_row("2. Consider if any instruction is counterproductive.")
        result_view.add_row("3. Consider order of instructions.")
        result_view.add_row("4. Consider external influences.")
        self.set_question_view(result_view)

    def set_question_view(self, view: QWidget):
        if self.question_view:
            self.question_view_container.layout().removeWidget(self.question_view)
        self.question_view = view
        self.question_view_container.layout().addWidget(view)

    def back(self):
        self.app.show_plan_selection()


class FormWidget(QWidget):
    def __init__(self):
        super(FormWidget, self).__init__()
        self.setLayout(QFormLayout())
        self.setStyleSheet("QLabel {font: 16pt}")

    def add_row(self, text: str, label: str = ""):
        self.layout().addRow(text, QLabel(label))

    def add_yes_no_buttons(self, yes_callback: Callable, no_callback: Callable):
        btn_bar = YesNoButtonBar()
        btn_bar.btn_yes.clicked.connect(yes_callback)
        btn_bar.btn_no.clicked.connect(no_callback)
        self.layout().addRow(btn_bar)

    def add_button(self, button: QPushButton):
        self.layout().addRow(button)


class YesNoButtonBar(QWidget):
    def __init__(self):
        super(YesNoButtonBar, self).__init__()
        self.setLayout(QHBoxLayout())
        self.btn_yes = QPushButton("Yes")
        self.btn_no = QPushButton("No")
        self.layout().addWidget(self.btn_yes)
        self.layout().addWidget(self.btn_no)
        self.layout().addStretch()


class DebuggingTreeView(QTreeWidget):

    color_std = QColor(0, 0, 0)
    color_highlight = QColor(0, 10, 100)
    color_valid = QColor(0, 150, 0)
    color_invalid = QColor(150, 0, 0)

    def __init__(self, tree: JasonDebuggingTreeNode):
        super(DebuggingTreeView, self).__init__()
        self.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.views = {}
        self.highlighted_view: Optional[QTreeWidgetItem] = None
        self.setHeaderLabels(["Debugging Tree"])

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
            DebuggingTreeView.color_node_view(view, color)

    @staticmethod
    def color_node_view(view: QTreeWidgetItem, color: QColor):
        view.setBackground(0, color)

    @staticmethod
    def highlight_view(view: QTreeWidgetItem):
        view.setBackground(0, DebuggingTreeView.color_highlight)

    def highlight_node(self, node: JasonDebuggingTreeNode):
        # if self.highlighted_view:
        #     self.color_node_view(self.highlighted_view, self.color_std)
        # self.highlighted_node = node
        self.color_node(node, DebuggingTreeView.color_highlight)

    def mark_validity(self, node: JasonDebuggingTreeNode, valid: bool):
        self.color_node(node, DebuggingTreeView.color_valid if valid else self.color_invalid)

    def mark_view(self, view: QTreeWidgetItem, valid: bool):
        self.color_node_view(view, DebuggingTreeView.color_valid if valid else self.color_invalid)

    def expand_node_with_plan_instructions(self, origin: JasonDebuggingTreeNode) -> dict[Instruction, QTreeWidgetItem]:
        parent_view = self.views[origin]
        parent_view.takeChildren()
        instructions = origin.im.instructions
        result: dict[Instruction, QTreeWidgetItem] = {}
        for instruction in instructions:
            node_view = DebuggingTreeView.create_node(str(instruction))
            result[instruction] = node_view
            if instruction.text.startswith("!"):
                self.color_node_view(node_view, DebuggingTreeView.color_valid)
            parent_view.addChild(node_view)
        self.expandAll()
        return result


class AgentStateView(QWidget):
    def __init__(self, agent_repo: AgentRepository, agent_name: str, start_cycle=0, start_label="Start", navigable=True):
        super(AgentStateView, self).__init__()
        self.agent_repo = agent_repo
        self.agent_name = agent_name
        self.agent_data = self.agent_repo.get_agent_data(self.agent_name)
        self.navigable = navigable
        self.start_cycle = start_cycle
        self.current_cycle = start_cycle

        self.setLayout(QVBoxLayout())

        self.belief_view = BeliefView()
        self.intention_view = IntentionView(self.agent_data)
        self.layout().addWidget(self.belief_view)
        self.layout().addWidget(self.intention_view)

        self.cycle_label = QLabel(str(start_cycle))
        self.bookmark_combo = QComboBox()
        self.bookmark_combo.setEditable(False)
        self.add_bookmark(start_cycle, start_label)
        btn_prev = QPushButton("Prev")
        btn_next = QPushButton("Next")
        btn_go = QPushButton("Go")
        cycle_bar = QWidget()
        QHBoxLayout(cycle_bar)
        cycle_bar.layout().addWidget(btn_prev)
        cycle_bar.layout().addWidget(self.cycle_label)
        cycle_bar.layout().addWidget(btn_next)
        bookmarks_widget = QWidget()
        QVBoxLayout(bookmarks_widget)
        bookmarks_widget.layout().addWidget(QLabel("Bookmarks"))
        bookmarks_widget.layout().addWidget(self.bookmark_combo)
        cycle_bar.layout().addWidget(bookmarks_widget)
        cycle_bar.layout().addWidget(btn_go)
        cycle_bar.layout().addStretch()
        btn_prev.clicked.connect(self.prev_cycle)
        btn_next.clicked.connect(self.next_cycle)
        btn_go.clicked.connect(self.goto_selected_bookmark)
        self.layout().addWidget(cycle_bar)
        self.show_cycle(self.start_cycle)

    def goto_selected_bookmark(self):
        if not self.bookmark_combo.currentText():
            return
        cycle = int(self.bookmark_combo.currentText().split(": ")[0])
        self.show_cycle(cycle)

    def add_bookmark(self, cycle: int, description: str):
        self.bookmark_combo.insertItem(100, f"{cycle}: {description}")

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
    def __init__(self, beliefs: Optional[list[str]] = None):
        super(BeliefView, self).__init__("Beliefs")
        self.tree.setColumnWidth(0, 1000)
        self.tree.setHeaderLabels(["Belief"])
        self.set_beliefs(beliefs)

    def set_beliefs(self, beliefs: list[str]):
        if beliefs:
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


class Bug:
    def __init__(self, reason: str, file: str, location: str, code=""):
        self.reason = reason
        self.file = file
        self.location = location
        self.code = code
