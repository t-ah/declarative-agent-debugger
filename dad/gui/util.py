import os

from PyQt6.QtWidgets import QFileDialog, QMessageBox, QTableView, QAbstractItemView


def get_path_from_user(path=""):
    dlg = QFileDialog()
    dlg.setFileMode(QFileDialog.FileMode.Directory)
    if path != "" and os.path.isdir(path):
        dlg.setDirectory(path)

    if dlg.exec():
        return dlg.selectedFiles()[0]
    return ""

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