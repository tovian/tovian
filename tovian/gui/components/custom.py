# -*- coding: utf-8 -*-

"""
Custom implementation of Qt Widgets for various purposes
"""

import logging

from PySide.QtGui import *
from PySide.QtCore import *


logger = logging.getLogger(__name__)
logger.debug('Import ' + __name__)


class DJumpQSlider(QSlider):
    """
    QSlider which implements mouse direct jump setValue.
    Where user clicks on slider, this value is immediately set.
    """

    def mousePressEvent(self, event):
        """
        :type event: PySide.QtGui.QMouseEvent
        """
        if event.button() == Qt.LeftButton:
            newValue = self.minimum() + round(((self.maximum()-self.minimum()) * event.x()) / float(self.width()))
            self.setValue(newValue)
            event.accept()

    def mouseMoveEvent(self, event):
        """
        :type event: PySide.QtGui.QMouseEvent
        """
        newValue = self.minimum() + round(((self.maximum()-self.minimum()) * event.x()) / float(self.width()))
        self.setValue(newValue)

    def mouseReleaseEvent(self, event):
        """
        :type event: PySide.QtGui.QMouseEvent
        """
        if event.button() == Qt.LeftButton:
            newValue = self.minimum() + round(((self.maximum()-self.minimum()) * event.x()) / float(self.width()))
            self.setValue(newValue)


class OddQSlider(DJumpQSlider):
    """
    QSlider which can be set only to odd value.
    Implements DirectJumpQSlider!
    """

    def setValue(self, value):
        """
        Sets only odd values! Even numbers are rounded up.
        :type value: int
        """
        value = value + 1 if value % 2 == 0 else value
        super(OddQSlider, self).setValue(value)



