# coding=utf-8
"""Resources test.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""

__author__ = 'james@element84.com'
__date__ = '2020-04-21'
__copyright__ = 'Copyright 2020,  NASA'

import unittest

from qgis.PyQt.QtGui import QIcon


class HarmonyQGISResourcesTest(unittest.TestCase):
    """Test rerources work."""

    def setUp(self):
        """Runs before each test."""
        pass

    def tearDown(self):
        """Runs after each test."""
        pass

    def test_icon_png(self):
        """Test we can make an icon."""
        path = ':/plugins/HarmonyQGIS/icon.png'
        icon = QIcon(path)
        self.assertFalse(icon.isNull())


def run_all():
    suite = unittest.makeSuite(HarmonyQGISResourcesTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
