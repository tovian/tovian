# -*- coding: utf-8 -*-

"""
Dialog form mask editing
"""

__version__ = "$Id: mask.py 348 2013-12-12 11:40:55Z herbig $"

import logging

from PySide.QtGui import *
from PySide.QtCore import *

from tovian.gui.forms import maskform
from tovian.gui.components.graphics import MaskCanvas
from tovian.gui.components.custom import OddQSlider, DJumpQSlider

logger = logging.getLogger(__name__)
logger.debug('Import ' + __name__)


class MaskDialog(QDialog, maskform.Ui_maskForm):

    dataExported = Signal(buffer, bool)

    def __init__(self, bgr_pixmap, x, y, width, height, mask_data=None, color=(255, 255, 255), parent=None):
        """
        :type bgr_pixmap: PySide.QtGui.QPixmap
        :type width: int
        :type height: int
        :type mask_data: buffer
        :type color: (int, int, int)
        :type parent: tovian.gui.dialogs.mainwindow.MainApp
        """
        super(MaskDialog, self).__init__(parent)

        self.brush_size = 11
        self.brush_opacity = 255
        self.brush_type = MaskCanvas.RECTANGLE
        self.is_new = False

        # process data and create RGBA image
        self.mask_width = width
        self.mask_height = height
        red, blue, green = color
        rgba = chr(red) + chr(blue) + chr(green) + '\x01'       # alpha channel value cant be zero!

        logger.debug("Creating template image with empty mask data")
        self.img_buffer = buffer(rgba*(self.mask_width*self.mask_height))
        self.mask_img = QImage(self.img_buffer, self.mask_width, self.mask_height, QImage.Format_ARGB32)

        # mask_data = buffer('\x80' * (self.mask_width*self.mask_height))
        if mask_data is not None:
            logger.debug("Loading mask data as alpha channel to image")
            alpha_img = QImage(mask_data, self.mask_width, self.mask_height, QImage.Format_Indexed8)
            self.mask_img.setAlphaChannel(alpha_img)
            self.is_new = True

        self.scene = QGraphicsScene(self)
        self.an_mask_item = MaskCanvas(image=self.mask_img,
                                       brush_size=self.brush_size,
                                       opacity=self.brush_opacity,
                                       brush_type=self.brush_type)
        self.bgr_pixmap_item = QGraphicsPixmapItem(bgr_pixmap)

        self.setupUi(self)
        self.setupSignals()

        QTimer.singleShot(0, self.afterInit)
        logger.debug("Mask editor dialog initialized")

    def setupUi(self, parent):
        super(MaskDialog, self).setupUi(parent)
        self.bgr_pixmap_item.setEnabled(False)
        self.scene.addItem(self.bgr_pixmap_item)
        self.scene.addItem(self.an_mask_item)

        self.graphicsView.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.graphicsView.setStyleSheet("background: #bfbfbf")
        self.graphicsView.setScene(self.scene)

        self.sizeSlider = DJumpQSlider(Qt.Horizontal, self)
        self.sizeSlider.setMaximum(100)
        self.sizeSlider.setMinimum(1)
        self.sizeSlider.setMinimumWidth(50)
        self.sizeSlider.setSingleStep(1)
        self.sizeSlider.setPageStep(5)
        self.sizeSlider.setValue(self.brush_size)
        self.opacitySlider = DJumpQSlider(Qt.Horizontal, self)
        self.opacitySlider.setMinimum(1)
        self.opacitySlider.setMaximum(255)
        self.opacitySlider.setMinimumWidth(50)
        self.opacitySlider.setValue(self.brush_opacity)

        self.toolbarLayout.insertWidget(2, self.opacitySlider)
        self.toolbarLayout.insertWidget(5, self.sizeSlider)
        self.graphicsView.resizeEvent = self.viewResized

        self.setWindowFlags(self.windowFlags() ^ Qt.WindowContextHelpButtonHint)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinMaxButtonsHint)

        self.sizeEdit.setText(unicode(self.brush_size))
        self.opacityEdit.setText(unicode(self.brush_opacity))

        self.cursor_rect_pixmap = QPixmap(":/icons/icons/cursor_rect.png")
        self.cursor_circle_pixmap = QPixmap(":/icons/icons/cursor_circle.png")
        if self.brush_type == MaskCanvas.RECTANGLE:
            self.cursor_current_pixmap = self.cursor_rect_pixmap
        elif self.brush_type == MaskCanvas.CIRCLE:
            self.cursor_current_pixmap = self.cursor_circle_pixmap
        else:
            raise NotImplementedError("Cursor for current brush type is not implemented!")

        self.graphicsView.setCursor(QCursor(self.cursor_current_pixmap))

    def setupSignals(self):
        self.sizeSlider.valueChanged.connect(self.setBrushSize)
        self.sizeEdit.editingFinished.connect(self.setBrushSize)
        self.opacitySlider.valueChanged.connect(self.setPenOpacity)
        self.opacityEdit.editingFinished.connect(self.setPenOpacity)
        self.hideBgrCheck.stateChanged.connect(self.hideShowBgr)
        self.saveBtn.clicked.connect(self.saveAndClose)
        self.brushTypeCombo.currentIndexChanged.connect(self.changeBrushType)

    @Slot()
    def afterInit(self):
        """
        Called when dialog is fully loaded to adjust dialog size depending on mask aspect ratio, etc.
        """
        parent_size = self.parent().size()
        border_height = self.height() - self.graphicsView.height()
        border_width = self.width() - self.graphicsView.width()
        bgr_aspect_ratio = self.mask_width / float(self.mask_height)

        new_height = round(0.8 * parent_size.height())
        gview_height = new_height - border_height
        gview_width = bgr_aspect_ratio * gview_height
        new_width = gview_width + border_width

        if new_width > parent_size.width():
            new_width = parent_size.width()
            gview_width = new_width - border_width
            gview_height = gview_width / float(bgr_aspect_ratio)
            new_height = gview_height + border_height

        logger.debug("Adjusting mask editor window size to %sx%s", new_width, new_height)
        self.resize(new_width, new_height)

        # center the dialog
        frect = self.frameGeometry()
        frect.moveCenter(self.parent().geometry().center())
        self.move(frect.topLeft())

    @Slot(QResizeEvent)
    def viewResized(self, event):
        """
        Called when QGraphicsView is resized
        :type event: QResizeEvent
        """
        QGraphicsView.resizeEvent(self.graphicsView, event)     # parent method
        self.graphicsView.fitInView(self.bgr_pixmap_item, Qt.KeepAspectRatio)
        self.graphicsView.fitInView(self.an_mask_item, Qt.KeepAspectRatio)
        self.updateCursor()

    @Slot(int)
    def setBrushSize(self, value=None):
        """
        Sets pen size from given value or from pen-size line edit.
        :type value: int or None
        """
        if value is None:
            try:
                value = int(self.sizeEdit.text())
            except ValueError:
                logger.debug("Wrong pen-size input format")
                QApplication.beep()
                self.sizeEdit.setFocus()
                self.sizeEdit.selectAll()
                return

        if self.sizeSlider.minimum() <= value <= self.sizeSlider.maximum():
            logger.debug("Setting new brush size value to %s", value)

            # sync line edit and slider
            self.sizeEdit.blockSignals(True)
            self.sizeEdit.setText(str(value))
            self.sizeEdit.blockSignals(False)
            self.sizeSlider.blockSignals(True)
            self.sizeSlider.setValue(value)
            self.sizeSlider.blockSignals(False)

            self.brush_size = value
            self.an_mask_item.changeBrushSize(value)
            self.updateCursor()
        else:
            logger.debug("Pen-size is out of range")
            QApplication.beep()
            self.sizeEdit.setFocus()
            self.sizeEdit.selectAll()

    @Slot(int)
    def setPenOpacity(self, value=None):
        """
        Sets pen opacity from given value or from pen-opacity line edit.
        :type value: int or None
        """
        if value is None:
            try:
                value = int(self.opacityEdit.text())
            except ValueError:
                logger.debug("Wrong pen-opacity input format")
                QApplication.beep()
                self.opacityEdit.setFocus()
                self.opacityEdit.selectAll()
                return

        if self.opacitySlider.minimum() <= value <= self.opacitySlider.maximum():
            logger.debug("Setting new opacity value to %s", value)

            # sync line edit and slider
            self.opacityEdit.blockSignals(True)
            self.opacityEdit.setText(str(value))
            self.opacityEdit.blockSignals(False)
            self.opacitySlider.blockSignals(True)
            self.opacitySlider.setValue(value)
            self.opacitySlider.blockSignals(False)

            self.brush_opacity = value
            self.an_mask_item.changeBrushOpacity(value)
        else:
            logger.debug("Pen-opacity is out of range")
            QApplication.beep()
            self.opacityEdit.setFocus()
            self.opacityEdit.selectAll()

    @Slot(Qt.CheckState)
    def hideShowBgr(self, state):
        """
        Called when user check 'Hide background' checkbox
        :type state: Qt.CheckState
        """
        logger.debug("Switching background visibility")
        if state == Qt.Checked:
            self.bgr_pixmap_item.setVisible(False)
        else:
            self.bgr_pixmap_item.setVisible(True)

    @Slot(int)
    def changeBrushType(self, index):
        """
        Called when user picks new brush type from combobox.
        :type index: int
        :raise NotImplementedError: When new index is not implemented.
        """
        logger.debug("Current brush type changed")

        if index == MaskCanvas.RECTANGLE:
            self.cursor_current_pixmap = self.cursor_rect_pixmap
            self.an_mask_item.changeBrushType(MaskCanvas.RECTANGLE)
        elif index == MaskCanvas.CIRCLE:
            self.cursor_current_pixmap = self.cursor_circle_pixmap
            self.an_mask_item.changeBrushType(MaskCanvas.CIRCLE)
        else:
            raise NotImplementedError("Current brush index is not implemented!")

        self.updateCursor()

    def updateCursor(self):
        """
        When cursor size, type or view size is changed, method is called to edit cursor type/size
        """
        transform = self.graphicsView.transform()
        scale = transform.m11()                     # scale_x == scale_y
        curs_size = round(self.brush_size * scale)

        max_size = max(self.graphicsView.width(), self.graphicsView.height())
        if curs_size > max_size:
            curs_size = max_size

        cursor = QCursor(self.cursor_current_pixmap.scaled(curs_size, curs_size, Qt.IgnoreAspectRatio, Qt.SmoothTransformation))
        self.graphicsView.setCursor(cursor)

    @Slot()
    def saveAndClose(self):
        """
        Called when saveBtn is clicked to export maskdata and close the window.
        """
        self.exportData()
        self.close()

    def closeEvent(self, event):
        """
        Called when dialog close event was invoked.
        If mask_item has been edited, user is prompted to save changes or discard.
        :type event: PySide.QtGui.QCloseEvent
        """
        logger.debug("Invoked close event")
        if self.an_mask_item.edited:
            save_dialog = QMessageBox(QMessageBox.Question, "Save changes", "")
            save_dialog.setWindowIcon(self.parent().windowIcon())
            save_dialog.setText("<b>" + "Do you want to save changes?" + "</b>")
            save_dialog.setInformativeText("Otherwise, all changes will be lost!")
            save = save_dialog.addButton(QMessageBox.Save)
            dont_save = save_dialog.addButton(QMessageBox.Discard)
            cancel = save_dialog.addButton(QMessageBox.Cancel)
            save_dialog.exec_()

            if save_dialog.clickedButton() is save:
                self.exportData()
            elif save_dialog.clickedButton() is cancel:
                event.ignore()
                return

        logger.debug("Cleaning up and closing mask editor")
        self.an_mask_item.cleanUp()
        event.accept()

    def exportData(self):
        """
        Called to export data from editor, then data could be saved to the annotationValue
        """
        logger.debug("Exporting data to buffer")
        self.an_mask_item.edited = False

        alpha_img = self.mask_img.alphaChannel()
        alpha_buffer = alpha_img.constBits()
        self.dataExported.emit(alpha_buffer, self.is_new)

