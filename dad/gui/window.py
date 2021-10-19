from PyQt6.QtWidgets import QMainWindow

from gui.home import HomeScreen
from gui.plan_selection import PlanSelectionScreen
from gui.debugging import DebuggingScreen


class MainWindow(QMainWindow):
    def __init__(self, app):
        super(MainWindow, self).__init__()
        self.app = app
        self.setGeometry(200, 200, 1024, 768)
        self.setWindowTitle("Declarative Agent Debugger")

    def show_home(self):
        self.setCentralWidget(HomeScreen(self.app))

    def show_plan_selection(self):
        self.setCentralWidget(PlanSelectionScreen(self.app))

    def show_debugging(self, folder):
        self.setCentralWidget(DebuggingScreen(self.app))