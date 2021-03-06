from PySide.QtCore import *
from PySide.QtGui import QTextEdit

#---------------------------------------------------------------------------------------------------
# Classes
#---------------------------------------------------------------------------------------------------
class QTextEditClick( QTextEdit):
    def Connect( self, func):
        self.connectFunc = func

    def mouseDoubleClickEvent( self, event):
        if event.button() == Qt.LeftButton:
            self.connectFunc()

