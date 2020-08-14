from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QTableWidgetItem, QFileDialog, QErrorMessage, QMessageBox
from qgis.core import QgsProject, QgsSettings, QgsVectorLayer, QgsVectorFileWriter, QgsCoordinateTransformContext, QgsRasterLayer, QgsMessageLog
import os.path
import json

sessionsKey = "saved_sessions"
newSessionTag = "<NEW SESSION>"
tempSavedSessions = None
currentSessionUpdated = False

def isCurrentSessionUpdated():
  global currentSessionUpdated
  return currentSessionUpdated

def setCurrentSessionUpdated(isUpdated):
  global currentSessionUpdated
  currentSessionUpdated = isUpdated

# update the buttons on the session dialog
def updateSessionsDlgButtons(mainDlg, dlg):
  if dlg.listWidget.currentItem():
    dlg.deletebutton.setEnabled(True)
    dlg.exportButton.setEnabled(True)
  else:
    dlg.deletebutton.setEnabled(False)
    dlg.exportButton.setEnabled(False)

def startDeleteSession(mainDlg, dlg):
  global tempSavedSessions
  settings = QgsSettings()
  savedSessions = settings.value(sessionsKey) or []
  tempSavedSessions = None
  if dlg.listWidget.currentItem():
    sessionName = dlg.listWidget.currentItem().text()
    tempSavedSessions = list(filter(lambda session : session[0] != sessionName, savedSessions))
    
    dlg.listWidget.clear()
    # add remaining items to list widget
    for [name, _sessionData] in tempSavedSessions:
      dlg.listWidget.addItem(name)
    if tempSavedSessions:
      finishDeleteSession(mainDlg)

def finishDeleteSession(dlg):
  if tempSavedSessions:
    settings = QgsSettings()
    settings.setValue(sessionsKey, tempSavedSessions)
    populateSessionsCombo(dlg)
    switchSession(dlg)
 
# when a session is imported the layer it refers to may not exist - if so replace it with 
# <None>
def replaceMissingLayers(session):
  layers = [l for l in QgsProject.instance().mapLayers().values() if l.type() == QgsVectorLayer.VectorLayer]
  layerNames = [layer.name() for layer in layers]
  if not session[1]['layer'] in layerNames:
    session[1]['layer'] = "<None>"
  return session

# check to see if a session with the given name exists in the saved sessions
def doesSessionNameExist(oldSessions, name):
  for session in oldSessions:
    if session[0] == name:
      return True
  return False

# add a new session to the saved sessions, renaming it by appending an index if necessary to avoid
# duplicate names
def addNewSession(oldSessions, newSession, index):
  name = newSession[0] + "_" + str(index)
  if doesSessionNameExist(oldSessions, name):
    return addNewSession(oldSessions, index + 1)
  return oldSessions.append(replaceMissingLayers([name, newSession[1]]))

def addNewSessions(newSessions):
  settings = QgsSettings()
  savedSessions = settings.value(sessionsKey) or []
  for session in newSessions:
    if doesSessionNameExist(savedSessions, session[0]):
      addNewSession(savedSessions, session, 1)
    else:
      savedSessions.append(session)
  settings.setValue(sessionsKey, savedSessions)
  return savedSessions

def importSessions(mainDlg, dlg, fileName = None):
  if not fileName:
    fileName, _filter = QFileDialog.getOpenFileName(dlg, 'Open sessions file', '', "Json files (*.json)")
  if fileName:
    newSessions = []
    try:
      with open(fileName) as f:
        newSessions = json.loads(f.read())
    except Exception as e:
      QMessageBox.critical(None, "Error!", "Failed to parse {}".format(fileName) )
    savedSessions = addNewSessions(newSessions)
    resetDialog(dlg, savedSessions)
    populateSessionsCombo(mainDlg)

def exportSessions(dlg, fileName = None):
  settings = QgsSettings()
  savedSessions = settings.value(sessionsKey) or []
  selectedSessions = dlg.listWidget.selectedItems() or []
  sessionsSet = set()
  for item in selectedSessions:
    sessionsSet.add(item.text())
  exportedSessions = []

  for session in savedSessions:
    if session[0] in sessionsSet:
      exportedSessions.append(session)

  if len(exportedSessions) > 0:
    jsonStr = json.dumps(exportedSessions, sort_keys=True, indent=4)
    if fileName == None:
      fileName, _filter = QFileDialog.getSaveFileName(dlg, 'Save file', '', "Json files (*.json)")

    # dialog will verify overwrite if needed so no need to check here
    if fileName:
      if not fileName.endswith(".json"):
        fileName = fileName + ".json"
      try:
        with open(fileName, 'w') as f:
          f.write(jsonStr)
      except Exception as e:
        QMessageBox.critical(None, "Error!", "Failed to export session data to {}".format(fileName))

def resetDialog(dlg, savedSessions):
  dlg.listWidget.clear()
  # add items
  for [name, _sessionData] in savedSessions:
    dlg.listWidget.addItem(name)

  dlg.deletebutton.setEnabled(False)
  dlg.exportButton.setEnabled(False)

def manageSessions(plugin):
  dialog = plugin.sessionsDlg
  settings = QgsSettings()
  savedSessions = settings.value(sessionsKey) or []
  
  resetDialog(dialog, savedSessions)

  # Run the dialog event loop
  result = dialog.exec_()
  if result:
    finishDeleteSession(plugin.dlg)
    dialog.close()

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
  dlg.comboBox.setCurrentText(sessionData["layer"])
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
  savedSessions = settings.value(sessionsKey) or []
  for session in savedSessions:
    if session[0] == sessionName:
      populateDialogFromSession(dlg, session[1])
      setCurrentSessionUpdated(False)
      break

def saveSession(dlg, sessionName):
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
