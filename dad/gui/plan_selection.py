import os
import json

from PyQt6.QtGui import QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import QPushButton, QHBoxLayout, QLabel, QDialog, QTableView, QWidget, QHBoxLayout, QVBoxLayout, QDialogButtonBox

from gui.util import setup_table


class PlanSelectionScreen(QWidget):

    def __init__(self, app):
        super(PlanSelectionScreen, self).__init__()

        self.PLAN_MODEL_LABELS = ["Label", "Trigger", "Context", "Body", "Times used"]
        self.app = app
        self.agent_data = {}
        self.agent_table = QTableView()
        self.plan_table = QTableView()
        self.plan_model = QStandardItemModel()
        self.selected_agent = None

        main_layout = QHBoxLayout(self)

        agent_pane = QWidget()
        main_layout.addWidget(agent_pane)
        agent_pane_layout = QVBoxLayout(agent_pane)
        agent_pane_layout.addWidget(QLabel("Agents"))

        agent_model = QStandardItemModel()
        setup_table(table=self.agent_table, model=agent_model, labels=["Name", "Platform", "Src"])
        self.agent_table.clicked.connect(self.update_plans)
        agent_pane_layout.addWidget(self.agent_table)
        
        plans_pane = QWidget()
        main_layout.addWidget(plans_pane)
        plans_pane_layout = QVBoxLayout(plans_pane)
        plans_pane_layout.addWidget(QLabel("Plans used"))

        plans_pane_layout.addWidget(self.plan_table)
        setup_table(table=self.plan_table, model=self.plan_model, labels=self.PLAN_MODEL_LABELS)
        self.plan_table.doubleClicked.connect(self.on_plan_double_clicked)

        folder = self.app.config.get("current_folder")
        agent_infos = []
        for filename in os.listdir(folder):
            if filename.endswith(".log"):
                log_file_path = os.path.join(folder, filename)
                with open(log_file_path, "r") as log_file:
                    log_info = json.loads(log_file.readline())
                    if log_info["entity"] == "agent":
                        agent_infos.append(log_info)
        for agent in agent_infos:
            row = [QStandardItem(agent[x]) for x in ["name", "platform", "src"]]
            agent_model.appendRow(row)

    def on_plan_double_clicked(self):
        selected_plan = self.plan_table.currentIndex().siblingAtColumn(0).data()
        self.app.show_debugging(selected_plan, self.selected_agent)
        # TODO use dialog later to differentiate options
        # IntentionSelectionDialog(selected_plan).exec()

    def update_plans(self):
        self.selected_agent = self.agent_table.currentIndex().siblingAtColumn(0).data()
        agent_data = self.app.agent_repo.get(self.selected_agent)
        self.plan_model.clear()
        self.plan_model.setHorizontalHeaderLabels(self.PLAN_MODEL_LABELS)
        for label, plan in agent_data["plans"].items():
            if plan["used"] == 0: continue
            self.plan_model.appendRow([QStandardItem(x) for x in [label, plan["trigger"], plan.get("ctx", "T"), plan["body"], str(plan["used"])]])


class IntentionSelectionDialog(QDialog):
    def __init__(self, selected_plan):
        super(IntentionSelectionDialog, self).__init__()

        message = QLabel(f"Selected plan\n{selected_plan}\n\nDebug specific intention or plan in general?")
        buttons = QDialogButtonBox.StandardButton.Cancel
        button_box = QDialogButtonBox(buttons)
        button_box.rejected.connect(self.close)

        button_intention = QPushButton("One intention using the plan")
        button_plan = QPushButton("Entire plan (all intentions using the plan)")

        # TODO switch to actual features later

        self.setWindowTitle("Intention selection.")
        self.layout = QVBoxLayout()
        self.layout.addWidget(message)
        self.layout.addWidget(button_intention)
        self.layout.addWidget(button_plan)
        self.layout.addWidget(button_box)
        self.setLayout(self.layout)