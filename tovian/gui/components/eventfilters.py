# -*- coding: utf-8 -*-

"""
Various event filters for filtering (catching) specific events on objects, where a filter is installed.
"""

from PySide.QtGui import QApplication, QGraphicsView, QToolTip
from PySide.QtCore import Signal, QObject, QEvent, Qt, QPoint


class GlobalFilter(QObject):
    """
    Event filter for filtering events (i.e. key events) on main dialog and its children
    """

    escapePressed = Signal()
    playKeyPressed = Signal()
    stopKeyPressed = Signal()
    muteKeyPressed = Signal()
    volumeUpKeyPressed = Signal()
    volumeDownKeyPressed = Signal()
    mouseWheel = Signal(int)

    def eventFilter(self, obj, event):
        """
        Handles every event on filtered object and its children
        :param event: custom event
        :param obj: receiver
        :type event: PySide.QtCore.QEvent
        :type obj: PySide.QtCore.QObject
        :return: if the event needs to be filtered (eaten)
        :rtype : bool
        """
        # --- KEY PRESS events ----
        if event.type() is QEvent.KeyPress:
            modifier = QApplication.queryKeyboardModifiers()        # get pressed modifier keys (ctrl, shift, alt, etc)

            # ESCAPE key
            if event.key() == Qt.Key_Escape:
                self.escapePressed.emit()

            # PLAY or SPACE key
            elif event.key() == Qt.Key_MediaPlay or event.key() == Qt.Key_Space:
                self.playKeyPressed.emit()

            # STOP key
            elif event.key() == Qt.Key_MediaStop:
                self.stopKeyPressed.emit()

            # CTRL + PLUS key pressed
            if event.key() == Qt.Key_Plus and modifier == Qt.ControlModifier:
                self.volumeUpKeyPressed.emit()
                return True
                # CTRL + MINUS key pressed
            if event.key() == Qt.Key_Minus and modifier == Qt.ControlModifier:
                self.volumeDownKeyPressed.emit()
                return True
                # CTRL + * key pressed
            if event.key() == Qt.Key_Asterisk and modifier == Qt.ControlModifier:
                self.muteKeyPressed.emit()
                return True

        return super(GlobalFilter, self).eventFilter(obj, event)


class AttributeTableFilter(QObject):
    """
    Event filter for filtering enter key press events, when editing records in tableWidget
    """

    # TODO Unused - delete

    enterPressed = Signal()

    def eventFilter(self, obj, event):
        """
        Handles every event on filtered object and filters Esc key press
        :param obj: receiver
        :type obj: PySide.QtCore.QObject
        :type event: PySide.QtCore.QEvent
        """

        if event.type() is QEvent.KeyRelease:
            # enter (return) key needs to be caught
            if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
                self.enterPressed.emit()

        return super(AttributeTableFilter, self).eventFilter(obj, event)


class PerFrameSeekerFilter(QObject):
    """
    Event filter for filtering mouse btn release events
    """

    LMouseRelease = Signal()
    LMousePress = Signal()

    def eventFilter(self, obj, event):
        """
        :type obj: PySide.QtGui.QSlider
        :type event: PySide.QtCore.QEvent
        """
        if event.type() is QEvent.MouseButtonPress and event.button() is Qt.LeftButton:
            self.LMousePress.emit()

        if event.type() is QEvent.MouseButtonRelease and event.button() is Qt.LeftButton:
            self.LMouseRelease.emit()

        return super(PerFrameSeekerFilter, self).eventFilter(obj, event)


class NonVisTableFilter(QObject):
    """
    Filter for catching left-mouse click on nonVisTable
    """

    LMouseRelease = Signal()

    def __init__(self, parent):
        """
        :type parent: tovian.gui.dialogs.mainwindow.MainApp
        """
        super(NonVisTableFilter, self).__init__(parent)

    def eventFilter(self, obj, event):
        """
        :type obj: PySide.QtGui.QTableWidget
        :type event: PySide.QtCore.QEvent
        """

        # TRACK MOUSE AND DISPLAY TOOLTIP WITH LOCAL AND GLOBAL TEXT
        if event.type() is QEvent.MouseMove:
            item = self.parent().nonVisTable.itemAt(event.pos())

            # if no item on mouse position, ignore event
            if item:
                row = item.row()
                column = item.column()
                # get object id on mouse position
                object_id, frame = self.parent().annotation.nonvis_table_records[row][column]

                # show tooltip if there is an object a the object has at least global or local text
                if object_id is not None:
                    an_object = self.parent().annotation.nonvis_objects_in_frame_range[object_id][0]
                    text_global, text_local = an_object.get_text(frame)
                    if text_global or text_local:
                        QToolTip.showText(event.globalPos(), text_global + '\n' + text_local)

        # TRACK LEFT_MOUSE RELEASE EVENT
        elif event.type() is QEvent.MouseButtonRelease and event.button() is Qt.LeftButton:
            self.LMouseRelease.emit()

        return QObject.eventFilter(self, obj, event)