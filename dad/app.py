import os
import sys
import json

from PyQt6.QtWidgets import QApplication, QMainWindow

from gui.home import HomeScreen
from gui.plan_selection import PlanSelectionScreen
from gui.debugging import DebuggingScreen
from model.agent import AgentRepository


class Application(QApplication):
    def __init__(self, args):
        super(Application, self).__init__(args)
        self.config = Config()
        self.agent_repo = AgentRepository(self.config)
        self.window = MainWindow(self)

    def start(self):
        self.window.show_home()
        self.window.show()
        sys.exit(self.exec())

    def show_home(self):
        self.window.setCentralWidget(HomeScreen(self))

    def show_plan_selection(self, folder):
        self.config.set("current_folder", folder)
        self.window.setCentralWidget(PlanSelectionScreen(self))

    def show_debugging(self, selected_plan):
        self.window.setCentralWidget(DebuggingScreen(self))


class MainWindow(QMainWindow):
    def __init__(self, app):
        super(MainWindow, self).__init__()
        self.app = app
        self.setGeometry(200, 200, 1280, 1024)
        self.setWindowTitle("Declarative Agent Debugger")


class Config():
    def __init__(self):
        if os.path.isfile("config.json"):
            with open("config.json", "r") as config_file:
                self.data = json.load(config_file)
        else:
            self.data = {
                "previous_folders": [],
                "current_folder": ""
            }

    def save(self):
        with open("config.json", "w") as config_file:
            json.dump(self.data, config_file)

    def get_previous_folders(self):
        return self.data["previous_folders"]

    def add_previous_folder(self, folder):
        previous_folders = self.data["previous_folders"]
        if folder not in previous_folders:
                previous_folders.insert(0, folder)
                previous_folders = previous_folders[:10]
                self.save()

    def set(self, key, value):
        self.data[key] = value
        self.save()

    def get(self, key):
        return self.data.get(key, "")


def main():
    app = Application(sys.argv)
    app.start()


if __name__ == "__main__":
    main()