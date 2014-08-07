# -*- coding: utf-8 -*-

"""
Simple dialog displays combobox with allowed annotation attributes for current object.
"""

import logging

from PySide.QtCore import Signal
from PySide.QtGui import QDialog

from tovian import models
from ..forms.attribselectform import Ui_attribSelection


logger = logging.getLogger(__name__)
logger.debug('Import ' + __name__)


class AttribSelectionDialog(QDialog, Ui_attribSelection):
    """
    Simple dialog displays combobox with allowed annotation attributes for current object
    """

    attributeSelected = Signal(models.entity.AnnotationAttribute)

    def __init__(self, attributes, parent):
        """
        :param attributes: attributes to display
        :param parent: parent dialog
        :type attributes: list of tovian.models.entity.AnnotationValue
        :type parent: PySide.QtGui.QWidget 
        """
        super(AttribSelectionDialog, self).__init__(parent)
        self.setupUi(self)

        self.accepted.connect(self.getAttrib)

        # setup combobox
        for attrib in attributes:
            self.attribComboBox.addItem(attrib.name, attrib)

        self.attribComboBox.setFocus()
        logger.debug("Attrib selection dialog initialized")

    def getAttrib(self):
        """
        When dialog accepted, method emits selected attribute
        """
        attrib = self.attribComboBox.itemData(self.attribComboBox.currentIndex())

        logger.debug("New attrib selected, emitting selected attrib")
        self.attributeSelected.emit(attrib)