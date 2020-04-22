from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QTableWidgetItem, QFileDialog, QErrorMessage, QMessageBox
from qgis.core import QgsProject, QgsSettings, QgsVectorLayer, QgsVectorFileWriter, QgsCoordinateTransformContext, QgsRasterLayer, QgsMessageLog

sessionsKey = "saved_sessions"

def handleSession(harmonyQGIS):
  fname, _filter = QFileDialog.getOpenFileName(harmonyQGIS.dlg, 'Open file', '/tmp', "JSON files (*.json)")
  QgsMessageLog.logMessage(fname, "Harmony Plugin")
  return fname

def doesSessionExist(sessionName):
  settings = QgsSettings()
  savedSessions = settings.value(sessionsKey) or []
  for [name, _session] in savedSessions:
    if name == sessionName:
      return True
  return False
  

def enterPressed(dlg):
  dlg.sessionCombo.setEditable(False)
  # check to see if a session with the given name already exists
  sessionName = dlg.sessionCombo.currentText()
  if doesSessionExist(sessionName):
    dlg.sessionCombo.removeItem(dlg.sessionCombo.currentIndex())
    dlg.sessionCombo.setEditable(False)
    errorDialog = QMessageBox.critical(dlg, "Error", "A session with that name already exists")
  
  saveSession(dlg)

def addSession(dlg):
  QgsMessageLog.logMessage("Adding session...", "Harmony Plugin")
  dlg.sessionCombo.setEditable(True)
  dlg.sessionCombo.lineEdit().clear()
  dlg.sessionCombo.lineEdit().setFocus()
  dlg.sessionCombo.lineEdit().editingFinished.connect(lambda:enterPressed(dlg))

def deleteSession(dlg):
  QgsMessageLog.logMessage("Deleting session...", "Harmony Plugin")
  sessionName = dlg.sessionCombo.currentText()
  dlg.sessionCombo.removeItem(dlg.sessionCombo.currentIndex())
  settings = QgsSettings()
  savedSessions = settings.value(sessionsKey)
  if savedSessions:
    savedSessions.pop(sessionName)
    settings.setValue(sessionsKey, settings)

def saveSession(dlg):
  sessionName = dlg.sessionCombo.currentText()
  QgsMessageLog.logMessage("Saving session " + sessionName, "Harmony Plugin")
  settings = QgsSettings()
  savedSessions = settings.value(sessionsKey) or []
  rowCount = dlg.tableWidget.rowCount()
  tableRows = []
  for row in range(rowCount):
      parameter = dlg.tableWidget.item(row, 0).text()
      value = dlg.tableWidget.item(row, 1).text()
      tableRows.append([parameter, value])
  session = {
    "collection": dlg.collectionField.text() or "",
    "version": dlg.versionField.text() or "",
    "variable": dlg.variableField.text() or "",
    "harmony_url": dlg.harmonyUrlLineEdit.text() or "",
    "layer": dlg.comboBox.currentText() or "<NONE>",
    "additional_parameters": tableRows
  }
  # savedSessions.add(sessionName)
  savedSessions.append([sessionName, session])
  settings.setValue(sessionsKey, savedSessions)
