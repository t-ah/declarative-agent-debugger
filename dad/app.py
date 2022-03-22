import sys

from PyQt6.QtWidgets import QApplication, QMainWindow

from config import Config
from gui.home import HomeScreen
from gui.goal_selection import GoalSelectionScreen
from gui.debugging import DebuggingScreen
from model.agent import AgentRepository


class Application(QApplication):
    def __init__(self, args):
        super(Application, self).__init__(args)
        self.config = Config()
        self.agent_repo = AgentRepository(self.config)
        self.window = MainWindow(self)

    def start(self):
        self.show_home()
        self.window.show()
        sys.exit(self.exec())

    def show_home(self):
        self.window.setCentralWidget(HomeScreen(self))

    def show_plan_selection(self, folder=None):
        if folder is None:
            folder = self.config.get("current_folder")
        else:
            self.config.set("current_folder", folder)
        self.window.setCentralWidget(GoalSelectionScreen(self.config, self.agent_repo, self.show_debugging))

    def show_debugging(self, selected_im: int, selected_agent: str):
        self.window.setCentralWidget(DebuggingScreen(self, selected_im, selected_agent))


class MainWindow(QMainWindow):
    def __init__(self, app):
        super(MainWindow, self).__init__()
        self.app = app
        self.resize(1920, 1024)
        self.frameGeometry().moveCenter(self.screen().availableGeometry().center())
        self.setWindowTitle("Declarative Agent Debugger")


def main():
    app = Application(sys.argv)
    app.start()


if __name__ == "__main__":
    main()
