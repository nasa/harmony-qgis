# coding=utf-8
"""Dialog test.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""

__author__ = 'james@element84.com'
__date__ = '2020-08-09'
__copyright__ = ('Copyright 2020, NASA')

import unittest

from qgis.PyQt import QtWidgets
from qgis.core import QgsSettings
import os.path

from harmony_qgis_dialog import HarmonyQGISDialog
from harmony_qgis_sessions_dialog import HarmonyQGISSessionsDialog
from harmony_qgis_sessions import saveSession, exportSessions, importSessions, resetDialog

from .utilities import get_qgis_app
QGIS_APP, CANVAS, IFACE, PARENT = get_qgis_app()

sessionsKey = "saved_sessions"
newSessionTag = "<NEW SESSION>"

expectedJSON = """[
    [
        "test_session",
        {
            "additional_parameters": [],
            "collection": "Collection123",
            "harmony_url": "",
            "layer": "MyPolyLayer",
            "variable": "red_var",
            "version": "1.0.0"
        }
    ]
]"""

def hasSession(name):
  settings = QgsSettings()
  savedSessions = settings.value(sessionsKey) or []
  for session in savedSessions:
    if session[0] == name:
      return True
  return False

class HarmonySessionsTest(unittest.TestCase):
    """Test sessions work."""

    def setUp(self):
      """Runs before each test."""
      self.dialog = HarmonyQGISDialog(None)
      self.sessionsDialog = HarmonyQGISSessionsDialog(None)
      settings = QgsSettings()
      settings.setValue(sessionsKey, [])
        
    def tearDown(self):
      """Runs after each test."""
      self.dialog = None

    def test_sessions(self):
      """Test we can save, export, and import a session."""
      field = self.dialog.collectionField
      field.insert("Collection123")
      field = self.dialog.versionField
      field.insert("1.0.0")
      field = self.dialog.variableField
      field.insert("red_var")

      comboBox = self.dialog.comboBox
      comboBox.clear()
      comboBox.addItem("MyPointLayer")
      comboBox.addItem("MyPolyLayer")
      comboBox.addItem("MyLineLayer")
      comboBox.setCurrentIndex(1)

      saveSession(self.dialog, "test_session")

      self.assertTrue(hasSession("test_session"))

      settings = QgsSettings()
      savedSessions = settings.value(sessionsKey) or []
      resetDialog(self.sessionsDialog, savedSessions)
      self.sessionsDialog.listWidget.setCurrentRow(0)

      fileName = "/tmp/test_sessions.json"
      exportSessions(self.sessionsDialog, fileName)
      self.assertTrue(os.path.exists(fileName))
      with open(fileName, "r") as f:
        contents = f.read()
        self.assertEqual(contents, expectedJSON)

      importSessions(self.dialog, self.sessionsDialog, fileName)
      savedSessions = settings.value(sessionsKey)
      self.assertEqual(len(savedSessions), 2)
      self.assertEqual(savedSessions[0][0], "test_session")
      self.assertEqual(savedSessions[1][0], "test_session_1")

def run_all():
    suite = unittest.makeSuite(HarmonySessionsTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

