from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtWidgets import QStyledItemDelegate, QLineEdit


class FloatDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        validator = QDoubleValidator(editor)
        validator.setNotation(QDoubleValidator.StandardNotation)
        validator.setDecimals(10)  # Adjust decimal places as needed
        validator.setBottom(0)
        editor.setMaxLength(12)
        editor.setValidator(validator)
        return editor
