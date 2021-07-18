# coding=utf-8
"""Dialog test.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""

__author__ = 'james@element84.com'
__date__ = '2020-04-21'
__copyright__ = ('Copyright 2020, NASA')

import unittest

from qgis.PyQt import QtWidgets

from harmony_qgis_dialog import HarmonyQGISDialog

from .utilities import get_qgis_app
QGIS_APP, CANVAS, IFACE, PARENT = get_qgis_app()


class HarmonyQGISDialogTest(unittest.TestCase):
    """Test dialog works."""

    def setUp(self):
        """Runs before each test."""
        self.dialog = HarmonyQGISDialog(None)

    def tearDown(self):
        """Runs after each test."""
        self.dialog = None

    def test_dialog_ok(self):
        """Test we can click OK."""
        field = self.dialog.collectionField
        field.insert("Collection123")
        field = self.dialog.versionField
        field.insert("1.0.0")
        field = self.dialog.variableField
        field.insert("red_var")

        comboBox = self.dialog.comboBox
        comboBox.clear()
        comboBox.addItem("MyPointLayer")
        comboBox.setCurrentIndex(0)

        button = self.dialog.button_box.button(QtWidgets.QDialogButtonBox.Ok)
        button.click()
        result = self.dialog.result()
        self.assertEqual(result, QtWidgets.QDialog.Accepted)

    def test_dialog_cancel(self):
        """Test we can click cancel."""
        button = self.dialog.button_box.button(
            QtWidgets.QDialogButtonBox.Cancel)
        button.click()
        result = self.dialog.result()
        self.assertEqual(result, QtWidgets.QDialog.Rejected)

    def test_collection_field(self):
        """Test we can set the collection field."""
        field = self.dialog.collectionField
        field.insert("Collection123")

        self.assertEqual(field.text(), "Collection123")

    def test_version_field(self):
        """Test we can set the version field."""
        field = self.dialog.versionField
        field.insert("1.0.0")

        self.assertEqual(field.text(), "1.0.0")

    def test_variable_field(self):
        """Test we can set the variable field."""
        field = self.dialog.variableField
        field.insert("red_var")

        self.assertEqual(field.text(), "red_var")

    def test_combobox(self):
        """Test we can set the layer combobox."""
        comboBox = self.dialog.comboBox
        comboBox.clear()
        comboBox.addItem("MyPointLayer")
        comboBox.addItem("MyPolyLayer")
        comboBox.addItem("MyLineLayer")
        comboBox.setCurrentIndex(1)

        self.assertEqual(comboBox.currentText(), "MyPolyLayer")


def run_all():
    suite = unittest.makeSuite(HarmonyQGISDialogTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
