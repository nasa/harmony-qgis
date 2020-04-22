from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QTableWidgetItem, QFileDialog, QErrorMessage, QMessageBox
from qgis.core import QgsProject, QgsSettings, QgsVectorLayer, QgsVectorFileWriter, QgsCoordinateTransformContext, QgsRasterLayer, QgsMessageLog

sessionsKey = "saved_sessions"
newSessionTag = "<NEW SESSION>"
tempSavedSessions = None

def startDeleteSession(mainDlg, dlg):
  global tempSavedSessions
  settings = QgsSettings()
  savedSessions = settings.value(sessionsKey) or []
  tempSavedSessions = None
  if dlg.listWidget.currentItem():
    sessionName = dlg.listWidget.currentItem().text()
    QgsMessageLog.logMessage("Deleting session " + sessionName, "Harmony Plugin")
    tempSavedSessions = list(filter(lambda session : session[0] != sessionName, savedSessions))
    
    dlg.listWidget.clear()
    # add remaining items to list widget
    for [name, _sessionData] in tempSavedSessions:
      dlg.listWidget.addItem(name)
    if tempSavedSessions:
      QgsMessageLog.logMessage("tempSavedSessions is not None", "Harmony Plugin")

def finishDeleteSession(dlg):
  if tempSavedSessions:
    QgsMessageLog.logMessage("Finishing deleting session", "Harmony Plugin")
    settings = QgsSettings()
    settings.setValue(sessionsKey, tempSavedSessions)
    populateSessionsCombo(dlg)
    switchSession(dlg)
  else:
    QgsMessageLog.logMessage("Nothing to do", "Harmony Plugin")

def manageSessions(plugin):
  dialog = plugin.sessionsDlg
  settings = QgsSettings()
  dialog.listWidget.clear()
  savedSessions = settings.value(sessionsKey) or []
  # add items
  for [name, _sessionData] in savedSessions:
    dialog.listWidget.addItem(name)
  
  # Run the dialog event loop
  result = dialog.exec_()
  if result:
    QgsMessageLog.logMessage("Updating sessions", "Harmony Plugin")
    finishDeleteSession(plugin.dlg)
    dialog.close()
  else:
    QgsMessageLog.logMessage("Cancel updating sessions", "Harmony Plugin")
    # dialog.close()

def populateSessionsCombo(dlg):
  settings = QgsSettings()
  savedSessions = settings.value(sessionsKey) or []
  dlg.sessionCombo.clear()
  dlg.sessionCombo.addItem(newSessionTag)
  for session in savedSessions:
    dlg.sessionCombo.addItem(session[0])

def clearDialog(dlg):
  dlg.collectionField.setText("")
  dlg.versionField.setText("")
  dlg.variableField.setText("")
  dlg.harmonyUrlLineEdit.setText("")
  dlg.tableWidget.setRowCount(0)

def populateDialogFromSession(dlg, sessionData):
  dlg.collectionField.setText(sessionData["collection"])
  dlg.versionField.setText(sessionData["version"])
  dlg.variableField.setText(sessionData["variable"])
  dlg.harmonyUrlLineEdit.setText(sessionData["harmony_url"])
  dlg.tableWidget.setRowCount(0)
  index = 0
  for row in sessionData["additional_parameters"]:
    dlg.tableWidget.insertRow(index)
    dlg.tableWidget.setItem(index, 0, QTableWidgetItem(row[0]))
    dlg.tableWidget.setItem(index, 1, QTableWidgetItem(row[1]))
    index = index + 1

def switchSession(dlg):
  settings = QgsSettings()
  sessionName = dlg.sessionCombo.currentText()
  if sessionName == newSessionTag:
    clearDialog(dlg)
  else:
    savedSessions = settings.value(sessionsKey) or []
    for session in savedSessions:
      if session[0] == sessionName:
        populateDialogFromSession(dlg, session[1])
        break

def saveSession(dlg, sessionName):
  # sessionName = dlg.sessionCombo.currentText()
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

  # update session if it exists before trying to insert it
  index = -1
  for sessionIndex in range(len(savedSessions)):
    existingSession = savedSessions[sessionIndex]
    if existingSession[0] == sessionName:
      index = sessionIndex
      break
  
  if index != -1:
    savedSessions[index] = [sessionName, session]
  else:
    savedSessions.append([sessionName, session])

  settings.setValue(sessionsKey, savedSessions)

# def handleSession(harmonyQGIS):
#   fname, _filter = QFileDialog.getOpenFileName(harmonyQGIS.dlg, 'Open file', '/tmp', "JSON files (*.json)")
#   QgsMessageLog.logMessage(fname, "Harmony Plugin")
#   return fname

# def doesSessionExist(sessionName):
#   settings = QgsSettings()
#   savedSessions = settings.value(sessionsKey) or []
#   for [name, _session] in savedSessions:
#     if name == sessionName:
#       return True
#   return False
  

# def enterPressed(dlg):
#   dlg.sessionCombo.setEditable(False)
#   # check to see if a session with the given name already exists
#   sessionName = dlg.sessionCombo.currentText()
#   if doesSessionExist(sessionName):
#     # dlg.sessionCombo.removeItem(dlg.sessionCombo.currentIndex())
#     dlg.sessionCombo.setEditable(False)
#     errorDialog = QMessageBox.critical(dlg, "Error", "A session with that name already exists")
#   else:
#     saveSession(dlg)

# def addSession(dlg):
#   QgsMessageLog.logMessage("Adding session...", "Harmony Plugin")
#   dlg.sessionCombo.setEditable(True)
#   dlg.sessionCombo.lineEdit().clear()
#   dlg.sessionCombo.lineEdit().setFocus()
#   dlg.sessionCombo.lineEdit().editingFinished.connect(lambda:enterPressed(dlg))

# def deleteSession(dlg):
#   QgsMessageLog.logMessage("Deleting session...", "Harmony Plugin")
#   sessionName = dlg.sessionCombo.currentText()
#   dlg.sessionCombo.removeItem(dlg.sessionCombo.currentIndex())
#   settings = QgsSettings()
#   savedSessions = settings.value(sessionsKey)
#   if savedSessions:
#     savedSessions.pop(sessionName)
#     settings.setValue(sessionsKey, settings)

