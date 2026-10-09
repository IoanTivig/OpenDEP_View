from PyQt6.QtCore import QEvent, QObject
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtWidgets import QAbstractScrollArea, QAbstractSpinBox, QApplication, QComboBox, QStyledItemDelegate, \
    QLineEdit, QWidget

from src.func.general import number_locale


# Spin boxes and drop-down lists do not change with the mouse wheel (a value changed by accident while scrolling the
# panel); the wheel scrolls the list behind them instead. Installed once on the application, so it covers every
# window. The open list of a drop-down is another widget and still scrolls.
class NoWheelChangeFilter(QObject):
    def eventFilter(self, obj, event):
        if event.type() != QEvent.Type.Wheel or not isinstance(obj, QWidget):
            return False
        inner_field = isinstance(obj, QLineEdit) and isinstance(obj.parentWidget(), (QAbstractSpinBox, QComboBox))
        if isinstance(obj, (QAbstractSpinBox, QComboBox)) or inner_field:
            # Passed to the nearest scroll area around it (a sent event is not handed on to the parents by Qt)
            parent = obj.parentWidget()
            while parent is not None and not isinstance(parent, QAbstractScrollArea):
                parent = parent.parentWidget()
            if parent is not None:
                QApplication.sendEvent(parent.viewport(), event)
            return True
        return False


class FloatDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        validator = QDoubleValidator(editor)
        # "." as decimal point and no thousands separator, and no limit on decimals: a value with more decimals
        # than the limit (e.g. 9755.664199597599 from a file) was "fixed up" on Enter into "9,755.6641995976",
        # which could not be read back
        validator.setLocale(number_locale())
        validator.setNotation(QDoubleValidator.Notation.ScientificNotation)
        validator.setDecimals(1000)
        editor.setMaxLength(32)
        editor.setValidator(validator)
        return editor
