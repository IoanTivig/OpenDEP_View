from PyQt5.QtWidgets import QApplication
from ui.main_ui import MainUI

app = QApplication([])
widget = MainUI()
widget.show()
app.exec_()
