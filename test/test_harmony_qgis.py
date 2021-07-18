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
from qgis.PyQt.QtCore import QVariant
from qgis.core import QgsVectorLayer, QgsFeature, QgsProject, QgsGeometry, QgsPointXY

from harmony_response import handleHarmonyResponse

from .utilities import get_qgis_app
from qgis.testing.mocked import get_iface


def hasLayer(layers, name):
    for layer in layers:
        if layer.name() == name:
            return True
    return False


class HarmonyQGISTest(unittest.TestCase):
    """Test plugin works."""

    def setUp(self):
        """Runs before each test."""
        self.harmony_qgis = plugins['harmony-qgis']
        self.harmony_qgis.setupGui()
        self.dialog = self.harmony_qgis.dlg

        # create a layer we can use to search with
        vl = QgsVectorLayer("Point", "MyPointLayer", "memory")
        pr = vl.dataProvider()
        f = QgsFeature()
        f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(-74, 51)))
        pr.addFeature(f)
        vl.updateExtents()
        QgsProject.instance().addMapLayer(vl)

        layerDict = QgsProject.instance().mapLayers()
        self.layerCount = len(layerDict)

    def tearDown(self):
        """Runs after each test."""
        self.harmony_qgis = None
        self.dialog = None

    def test_plugin(self):
        """Test we can retrieve layers from Harmony with the plugin (this is a SLOW test)."""

        self.assertIsNotNone(self.dialog)

        # fill in the request fields and choose our layer
        collectionField = self.dialog.collectionField
        collectionField.insert("C1233800302-EEDTEST")
        versionField = self.dialog.versionField
        versionField.insert("1.0.0")
        variableField = self.dialog.variableField
        variableField.insert("red_var")
        comboBox = self.dialog.comboBox
        comboBox.clear()
        comboBox.addItem("MyPointLayer")
        comboBox.setCurrentIndex(0)

        # run the request
        self.harmony_qgis.getResults(background=False)

        # check to see if the layers were created
        layerDict = QgsProject.instance().mapLayers()
        self.assertEqual(len(layerDict), self.layerCount + 20)
        self.assertTrue(hasLayer(layerDict.values(),
                        '001_00_7f00ff_global_red_var'))


def run_all():
    suite = unittest.makeSuite(HarmonyQGISTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
