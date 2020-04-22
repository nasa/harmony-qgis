# This Python file uses the following encoding: utf-8
from PyQt5 import QtCore
from PyQt5 import QtWidgets

class HarmonyEventFilter(QtCore.QObject):
    def __init__(self, plugin):
        super(HarmonyEventFilter, self).__init__(None)
        self.plugin = plugin

    def eventFilter(self, obj, event):
        if obj is self.plugin.dlg:
            if event.type() == QtCore.QEvent.KeyPress:
                if event.key() in (QtCore.Qt.Key_Return, 
                    QtCore.Qt.Key_Escape, 
                    QtCore.Qt.Key_Enter,):
                    return True
            if event.type() == QtCore.QEvent.Close:
                event.ignore()
                return True
        # return super(self.plugin.iface.mainWindow(), self).eventFilter(obj, event)
        return False