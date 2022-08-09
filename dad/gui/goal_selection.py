import json
import os
from typing import Callable

from PyQt6.QtGui import QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import QLabel, QDialog, QTableView, QWidget, QHBoxLayout, QVBoxLayout, \
    QDialogButtonBox, QSplitter, QTabWidget

from config import Config
from gui.util import setup_table, clear_model
from model.agent import AgentRepository, AgentData


class GoalSelectionScreen(QWidget):

    def __init__(self, config: Config, agent_repo: AgentRepository, callback_goal_selected: Callable[[int, str], None]):
        super(GoalSelectionScreen, self).__init__()

        self.config = config
        self.agent_repo = agent_repo
        self.callback_goal_selected = callback_goal_selected
        self.agent_table = QTableView()
        self.plan_table = QTableView()
        self.plan_model = QStandardItemModel()
        self.goal_table = QTableView()
        self.goal_model = QStandardItemModel()
        self.intention_table = QTableView()
        self.intention_model = QStandardItemModel()
        self.selected_agent = None
        QHBoxLayout(self)
        self.tab_widget = QTabWidget()

        agent_pane = QWidget()
        QVBoxLayout(agent_pane)
        agent_pane.layout().addWidget(QLabel("Agents"))

        agent_model = QStandardItemModel()
        setup_table(table=self.agent_table, model=agent_model,
                    labels=["Name", "Platform", "Src"],
                    column_widths=[150, 100, 250])
        self.agent_table.clicked.connect(self.update_agent_selected)
        agent_pane.layout().addWidget(self.agent_table)

        folder = self.config.get("current_folder")
        agent_info = []
        for filename in os.listdir(folder):
            if filename.endswith(".log"):
                log_file_path = os.path.join(folder, filename)
                with open(log_file_path, "r") as log_file:
                    log_info = json.loads(log_file.readline())
                    if log_info["entity"] == "agent":
                        agent_info.append(log_info)
        for agent in agent_info:
            row = [QStandardItem(agent[x]) for x in ["name", "platform", "src"]]
            agent_model.appendRow(row)
        if agent_info:
            self.agent_table.selectRow(0)
            self.update_agent_selected()

        self.tab_widget.addTab(self.intention_table, "Intentions")
        setup_table(table=self.intention_table, model=self.intention_model,
                    labels=["#", "Trigger", "Context", "Posted", "Selected"],
                    column_widths=[50, 300, 250, 70, 70])
        self.intention_table.doubleClicked.connect(self.on_intention_double_clicked)

        self.tab_widget.addTab(self.goal_table, "Goals")
        setup_table(table=self.goal_table, model=self.goal_model,
                    labels=["#", "Trigger", "Context", "Posted", "Selected"],
                    column_widths=[50, 300, 250, 70, 70])
        self.goal_table.doubleClicked.connect(self.on_goal_double_clicked)

        self.tab_widget.addTab(self.plan_table, "Plans")
        setup_table(table=self.plan_table, model=self.plan_model,
                    labels=["Label", "Trigger", "Context", "Body", "Times used"],
                    column_widths=[300, 250, 250])
        self.plan_table.doubleClicked.connect(self.on_plan_double_clicked)

        goal_selection_pane = QWidget()
        QVBoxLayout(goal_selection_pane)
        goal_selection_pane.layout().addWidget(QLabel("Select goal to debug:"))
        goal_selection_pane.layout().addWidget(self.tab_widget)

        splitter = QSplitter()
        self.layout().addWidget(splitter)
        splitter.addWidget(agent_pane)
        splitter.addWidget(goal_selection_pane)
        splitter.setSizes([200, 500])

    def on_intention_double_clicked(self):
        selected_goal = int(self.intention_table.currentIndex().siblingAtColumn(0).data())
        self.callback_goal_selected(selected_goal, self.selected_agent)

    def on_goal_double_clicked(self):
        selected_goal = int(self.goal_table.currentIndex().siblingAtColumn(0).data())
        self.callback_goal_selected(selected_goal, self.selected_agent)

    def on_plan_double_clicked(self):
        selected_plan_label = self.plan_table.currentIndex().siblingAtColumn(0).data()
        dialog = GoalSelectionDialog(self.agent_repo.get_agent_data(self.selected_agent), selected_plan_label)
        dialog.exec()
        if dialog.selected_goal != -1:
            self.callback_goal_selected(dialog.selected_goal, self.selected_agent)

    def update_agent_selected(self):
        self.selected_agent = self.agent_table.currentIndex().siblingAtColumn(0).data()
        agent_data: AgentData = self.agent_repo.get_agent_data(self.selected_agent)
        clear_model(self.intention_model)
        clear_model(self.goal_model)
        clear_model(self.plan_model)
        for _, intention in agent_data.intentions.items():
            if not intention.means:
                continue
            im = intention.means[0]
            self.intention_model.appendRow(
                QStandardItem(x) for x in [str(im.id), im.trigger, im.context, im.get_event_added(), str(im.start)])
        for _, im in agent_data.intended_means.items():
            self.goal_model.appendRow(
                QStandardItem(x) for x in [str(im.id), im.trigger, im.context, im.get_event_added(), str(im.start)])
        for label, plan in agent_data.plans.items():
            if plan.used == 0:
                continue
            self.plan_model.appendRow(
                QStandardItem(x) for x in [label, plan.trigger, plan.context, plan.body, str(plan.used)])


class GoalSelectionDialog(QDialog):
    def __init__(self, agent_data: AgentData, plan_label):
        super(GoalSelectionDialog, self).__init__()

        self.selected_goal = -1

        message = QLabel(f"Selected plan\n{plan_label}\n\nSelect goal to debug:")
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        button_box.rejected.connect(self.cancel)

        self.resize(1280, 1024)
        self.setWindowTitle("Goal selection.")
        QVBoxLayout(self)
        self.layout().addWidget(message)
        self.layout().addWidget(button_box)

        self.table = QTableView()
        model = QStandardItemModel()
        setup_table(self.table, model, ["#", "Trigger", "Context", "Posted", "Selected"], False, [50, 300, 250, 70, 70])
        self.layout().addWidget(self.table)
        self.table.doubleClicked.connect(self.on_goal_selected)

        for im in agent_data.intended_means.values():
            if im.plan.label == plan_label:
                model.appendRow(
                    QStandardItem(x) for x in [str(im.id), im.trigger, im.context, str(im.event.cycle_added), str(im.start)])

    def on_goal_selected(self):
        self.selected_goal = int(self.table.currentIndex().siblingAtColumn(0).data())
        self.close()

    def cancel(self):
        self.close()
