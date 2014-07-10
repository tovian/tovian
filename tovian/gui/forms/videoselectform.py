# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'uic_files/video-select.ui'
#
# Created: Mon Mar 10 11:13:37 2014
#      by: pyside-uic 0.2.15 running on PySide 1.2.1
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_VideoSelection(object):
    def setupUi(self, VideoSelection):
        VideoSelection.setObjectName("VideoSelection")
        VideoSelection.resize(790, 360)
        VideoSelection.setMinimumSize(QtCore.QSize(245, 200))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/icons/app_icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        VideoSelection.setWindowIcon(icon)
        self.verticalLayout = QtGui.QVBoxLayout(VideoSelection)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.selectVideoLbl = QtGui.QLabel(VideoSelection)
        self.selectVideoLbl.setObjectName("selectVideoLbl")
        self.horizontalLayout.addWidget(self.selectVideoLbl)
        self.userNameLbl = QtGui.QLabel(VideoSelection)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.userNameLbl.sizePolicy().hasHeightForWidth())
        self.userNameLbl.setSizePolicy(sizePolicy)
        self.userNameLbl.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.userNameLbl.setObjectName("userNameLbl")
        self.horizontalLayout.addWidget(self.userNameLbl)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.videoTable = QtGui.QTableWidget(VideoSelection)
        self.videoTable.setFrameShape(QtGui.QFrame.StyledPanel)
        self.videoTable.setFrameShadow(QtGui.QFrame.Sunken)
        self.videoTable.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.videoTable.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.videoTable.setTabKeyNavigation(False)
        self.videoTable.setAlternatingRowColors(True)
        self.videoTable.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.videoTable.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.videoTable.setShowGrid(True)
        self.videoTable.setGridStyle(QtCore.Qt.DotLine)
        self.videoTable.setRowCount(10)
        self.videoTable.setColumnCount(4)
        self.videoTable.setObjectName("videoTable")
        self.videoTable.setColumnCount(4)
        self.videoTable.setRowCount(10)
        item = QtGui.QTableWidgetItem()
        self.videoTable.setHorizontalHeaderItem(0, item)
        item = QtGui.QTableWidgetItem()
        self.videoTable.setHorizontalHeaderItem(1, item)
        item = QtGui.QTableWidgetItem()
        self.videoTable.setHorizontalHeaderItem(2, item)
        item = QtGui.QTableWidgetItem()
        self.videoTable.setHorizontalHeaderItem(3, item)
        self.videoTable.horizontalHeader().setVisible(True)
        self.videoTable.horizontalHeader().setCascadingSectionResizes(False)
        self.videoTable.horizontalHeader().setDefaultSectionSize(192)
        self.videoTable.horizontalHeader().setStretchLastSection(False)
        self.videoTable.verticalHeader().setVisible(False)
        self.videoTable.verticalHeader().setDefaultSectionSize(25)
        self.videoTable.verticalHeader().setStretchLastSection(False)
        self.verticalLayout.addWidget(self.videoTable)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.infoIcon = QtGui.QLabel(VideoSelection)
        self.infoIcon.setEnabled(True)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.infoIcon.sizePolicy().hasHeightForWidth())
        self.infoIcon.setSizePolicy(sizePolicy)
        self.infoIcon.setMinimumSize(QtCore.QSize(0, 0))
        self.infoIcon.setMaximumSize(QtCore.QSize(32, 32))
        self.infoIcon.setBaseSize(QtCore.QSize(0, 0))
        self.infoIcon.setText("")
        self.infoIcon.setPixmap(QtGui.QPixmap(":/icons/icons/info16.png"))
        self.infoIcon.setObjectName("infoIcon")
        self.horizontalLayout_2.addWidget(self.infoIcon)
        self.warningLbl = QtGui.QLabel(VideoSelection)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.warningLbl.sizePolicy().hasHeightForWidth())
        self.warningLbl.setSizePolicy(sizePolicy)
        self.warningLbl.setObjectName("warningLbl")
        self.horizontalLayout_2.addWidget(self.warningLbl)
        self.buttonBox = QtGui.QDialogButtonBox(VideoSelection)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Open)
        self.buttonBox.setObjectName("buttonBox")
        self.horizontalLayout_2.addWidget(self.buttonBox)
        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.retranslateUi(VideoSelection)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), VideoSelection.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), VideoSelection.reject)
        QtCore.QMetaObject.connectSlotsByName(VideoSelection)

    def retranslateUi(self, VideoSelection):
        VideoSelection.setWindowTitle(QtGui.QApplication.translate("VideoSelection", "Videos to annotate", None, QtGui.QApplication.UnicodeUTF8))
        self.selectVideoLbl.setText(QtGui.QApplication.translate("VideoSelection", "Select a video:", None, QtGui.QApplication.UnicodeUTF8))
        self.userNameLbl.setText(QtGui.QApplication.translate("VideoSelection", "user", None, QtGui.QApplication.UnicodeUTF8))
        self.videoTable.setSortingEnabled(False)
        self.videoTable.horizontalHeaderItem(0).setText(QtGui.QApplication.translate("VideoSelection", "Name", None, QtGui.QApplication.UnicodeUTF8))
        self.videoTable.horizontalHeaderItem(1).setText(QtGui.QApplication.translate("VideoSelection", "Comment", None, QtGui.QApplication.UnicodeUTF8))
        self.videoTable.horizontalHeaderItem(2).setText(QtGui.QApplication.translate("VideoSelection", "Active", None, QtGui.QApplication.UnicodeUTF8))
        self.videoTable.horizontalHeaderItem(3).setText(QtGui.QApplication.translate("VideoSelection", "Downloaded", None, QtGui.QApplication.UnicodeUTF8))
        self.warningLbl.setText(QtGui.QApplication.translate("VideoSelection", "Information", None, QtGui.QApplication.UnicodeUTF8))

import icons_rc