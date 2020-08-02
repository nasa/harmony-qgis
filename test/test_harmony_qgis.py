# coding=utf-8
"""Dialog test.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""

__author__ = 'james@element84.com'
__date__ = '2020-07-29'
__copyright__ = ('Copyright 2020, NASA')

import unittest

from qgis.PyQt import QtWidgets
from qgis.utils import plugins

# from harmony_qgis import HarmonyQGIS
from harmony_response import handleHarmonyResponse

from .utilities import get_qgis_app
# QGIS_APP, CANVAS, IFACE, PARENT = get_qgis_app()
from qgis.testing.mocked import get_iface


class HarmonyQGISTest(unittest.TestCase):
    """Test plugin works."""

    def setUp(self):
        """Runs before each test."""
        qgis_app, canvas, iface, parent = get_qgis_app()
        self.qgis_app = qgis_app
        print ("PLUGINS=================================")
        print(plugins)
        print(dir (plugins['harmony-qgis']))
        print ("====================PLUGINS=================================")
        self.harmony_qgis = plugins['harmony-qgis']
        # self.iface = get_iface()
        # self.plugin = HarmonyQGIS(self.iface)

    def tearDown(self):
        """Runs after each test."""
        # self.iface = None
        self.plugin = None

    def test_dialog_ok(self):
        """Test we can click OK."""
        
        print(type(self.qgis_app))
        dir(self.qgis_app)
        # self.assertIsNotNone(self.iface)
        self.assertIsNotNone(self.qgis_app)

        # self.harmony_qgis.run()

        self.dialog = self.harmony_qgis.dlg

        self.assertIsNotNone(self.dialog)
        

        # self.assertIsNotNone(self.plugin)
        # self.plugin.run()
        # button = self.dlg.button_box.button(QtWidgets.QDialogButtonBox.Ok)
        # button.click()
        # result = self.plugin.dlg.result()
        # self.assertEqual(result, QtWidgets.QDialog.Accepted)
        self.assertEqual(1,1)

    # def test_collection_field(self):
    #     """Test we can set the collection field."""

    #     field = self.dialog.collectionField
    #     field.insert("Collection123")

    #     self.assertEqual(field.text(), "Collection123")

    # def test_dialog_cancel(self):
    #     """Test we can click cancel."""
    #     button = self.dialog.button_box.button(QtWidgets.QDialogButtonBox.Cancel)
    #     button.click()
    #     result = self.dialog.result()
    #     self.assertEqual(result, QtWidgets.QDialog.Rejected)

def run_all():
    suite = unittest.makeSuite(HarmonyQGISTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

