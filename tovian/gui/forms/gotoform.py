# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'uic_files\goto.ui'
#
# Created: Mon Nov 18 14:00:26 2013
#      by: pyside-uic 0.2.15 running on PySide 1.2.1
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_gotoDialog(object):
    def setupUi(self, gotoDialog):
        gotoDialog.setObjectName("gotoDialog")
        gotoDialog.resize(250, 114)
        self.verticalLayout = QtGui.QVBoxLayout(gotoDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.valueLabel = QtGui.QLabel(gotoDialog)
        self.valueLabel.setObjectName("valueLabel")
        self.verticalLayout.addWidget(self.valueLabel)
        self.valueEdit = QtGui.QLineEdit(gotoDialog)
        self.valueEdit.setObjectName("valueEdit")
        self.verticalLayout.addWidget(self.valueEdit)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.frameRBtn = QtGui.QRadioButton(gotoDialog)
        self.frameRBtn.setChecked(True)
        self.frameRBtn.setObjectName("frameRBtn")
        self.horizontalLayout.addWidget(self.frameRBtn)
        self.timeRBtn = QtGui.QRadioButton(gotoDialog)
        self.timeRBtn.setObjectName("timeRBtn")
        self.horizontalLayout.addWidget(self.timeRBtn)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.buttonBox = QtGui.QDialogButtonBox(gotoDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(gotoDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), gotoDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), gotoDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(gotoDialog)

    def retranslateUi(self, gotoDialog):
        gotoDialog.setWindowTitle(QtGui.QApplication.translate("gotoDialog", "Go to", None, QtGui.QApplication.UnicodeUTF8))
        self.valueLabel.setText(QtGui.QApplication.translate("gotoDialog", "Go to frame:", None, QtGui.QApplication.UnicodeUTF8))
        self.valueEdit.setPlaceholderText(QtGui.QApplication.translate("gotoDialog", "Frame number...", None, QtGui.QApplication.UnicodeUTF8))
        self.frameRBtn.setToolTip(QtGui.QApplication.translate("gotoDialog", "Frame numer", None, QtGui.QApplication.UnicodeUTF8))
        self.frameRBtn.setText(QtGui.QApplication.translate("gotoDialog", "Frame", None, QtGui.QApplication.UnicodeUTF8))
        self.timeRBtn.setToolTip(QtGui.QApplication.translate("gotoDialog", "Float time value", None, QtGui.QApplication.UnicodeUTF8))
        self.timeRBtn.setText(QtGui.QApplication.translate("gotoDialog", "Time", None, QtGui.QApplication.UnicodeUTF8))

