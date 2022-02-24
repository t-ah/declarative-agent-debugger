from PyQt6.QtWidgets import QFileDialog, QMessageBox, QTableView, QAbstractItemView


def get_path_from_user(parent=None, path="", caption="Select directory"):
    return QFileDialog.getExistingDirectory(parent=parent, caption=caption, directory=path)


def info(message, parent=None):
    QMessageBox.information(parent, "Attention", message)


def setup_table(table=None, model=None, labels=None, edit=False, column_widths=None):
    if column_widths is None:
        column_widths = []
    if labels is None:
        labels = []
    if table is None:
        table = QTableView()
    if model is not None:
        model.setHorizontalHeaderLabels(labels)
        table.setModel(model)
    if not edit:
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    for i, width in enumerate(column_widths):
        table.setColumnWidth(i, width)
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    return table


def clear_model(model):
    model.removeRows(0, model.rowCount())
