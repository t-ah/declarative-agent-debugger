import os

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QListView, QHBoxLayout
from PyQt6.QtGui import QStandardItemModel, QStandardItem

from gui.util import get_path_from_user, info


class HomeScreen(QWidget):
    def __init__(self, app):
        super(HomeScreen, self).__init__()
        self.app = app

        layout = QVBoxLayout()
        self.setLayout(layout)

        button_bar = QWidget()
        QHBoxLayout(button_bar)
        open_button = QPushButton("Open new", button_bar)
        open_button.clicked.connect(self.on_open_button_clicked)
        button_bar.layout().addStretch()

        self.previous_folder_list = QListView()
        self.previous_folder_list.doubleClicked.connect(self.on_list_double_clicked)
        model = QStandardItemModel()
        self.previous_folder_list.setModel(model)
        for folder in self.app.config.get_previous_folders():
            item = QStandardItem(folder)
            model.appendRow(item)

        layout.addWidget(button_bar)
        layout.addWidget(self.previous_folder_list)

    def on_open_button_clicked(self):
        current_folder = self.app.config.get("current_folder")
        folder = get_path_from_user(parent=self, caption="Select log directory",
                                    path=current_folder[:current_folder.rfind("/")])
        if folder != "":
            self.app.config.add_previous_folder(folder)
            self.app.show_plan_selection(folder)
        else:
            print(f"Expected to get a directory, but got: {folder}")

    def on_list_double_clicked(self):
        folder = self.previous_folder_list.currentIndex().data()
        if os.path.isdir(folder):
            self.app.show_plan_selection(folder)
        else:
            info("Directory does not exist anymore.", parent=self)
