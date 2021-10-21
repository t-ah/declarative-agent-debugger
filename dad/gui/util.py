import os

from PyQt6.QtWidgets import QFileDialog, QMessageBox, QTableView, QAbstractItemView


def get_path_from_user(parent=None, path="", caption="Select directory"):
    return QFileDialog.getExistingDirectory(parent=parent, caption=caption, directory=path)

def info(message):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Information)
    msg.text = message
    msg.windowTitle = "Attention"
    msg.standardButtons = QMessageBox.StandardButton.Ok
    msg.exec()

def setup_table(table=None, model=None, labels=[], edit=False):
    if table == None:
        table = QTableView()
    if model != None:
        model.setHorizontalHeaderLabels(labels)
        table.setModel(model)
    if not edit:
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    return table