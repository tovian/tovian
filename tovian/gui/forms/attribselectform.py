# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\uic_files\attribute-selection.ui'
#
# Created: Sun Sep 08 15:17:45 2013
#      by: pyside-uic 0.2.15 running on PySide 1.2.1
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_attribSelection(object):
    def setupUi(self, attribSelection):
        attribSelection.setObjectName("attribSelection")
        attribSelection.resize(280, 92)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/icons/app_icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        attribSelection.setWindowIcon(icon)
        attribSelection.setModal(True)
        self.verticalLayout = QtGui.QVBoxLayout(attribSelection)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtGui.QLabel(attribSelection)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.attribComboBox = QtGui.QComboBox(attribSelection)
        self.attribComboBox.setObjectName("attribComboBox")
        self.verticalLayout.addWidget(self.attribComboBox)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.buttonBox = QtGui.QDialogButtonBox(attribSelection)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(attribSelection)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), attribSelection.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), attribSelection.reject)
        QtCore.QMetaObject.connectSlotsByName(attribSelection)

    def retranslateUi(self, attribSelection):
        attribSelection.setWindowTitle(QtGui.QApplication.translate("attribSelection", "Attribute selection", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("attribSelection", "Select an attribute:", None, QtGui.QApplication.UnicodeUTF8))

import icons_rc
