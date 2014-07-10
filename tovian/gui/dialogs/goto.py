# -*- coding: utf-8 -*-

"""
Simple dialog displays editbox with frame/time switch
"""

__version__ = "$Id: goto.py 347 2013-12-10 15:41:12Z herbig $"

import logging

from PySide.QtCore import *
from PySide.QtGui import *

from ..forms.gotoform import Ui_gotoDialog

logger = logging.getLogger(__name__)
logger.debug('Import ' + __name__)


class GoToDialog(QDialog, Ui_gotoDialog):
    """
    Simple dialog displays editbox with frame/time switch
    """

    newTimeSelected = Signal(float)

    def __init__(self, fps, frame_count, video_duration, memorized_pos, parent):
        """
        :type fps: float
        :type frame_count: int
        :type video_duration: float
        :type memorized_pos: (int, int)
        :type parent: tovian.gui.dialogs.mainwindow.MainApp
        """
        super(GoToDialog, self).__init__(parent)
        self.setupUi(self)

        self.fps = fps
        self.frame_count = frame_count
        self.video_duration = video_duration
        self.is_frame = True
        self.user_edited = False
        self.memorized_pos = memorized_pos

        self.frameRBtn.toggled.connect(self.valueTypeChanged)
        self.valueEdit.textEdited.connect(self.textEdited)

        self.valueTypeChanged(self.frameRBtn.isChecked())
        logger.debug("Goto dialog initialized.")

    @Slot()
    def valueTypeChanged(self, frame_checked):
        """
        Called when value on radio button is toggled
        :param frame_checked: if frame option is checked
        :type frame_checked: bool
        """
        if frame_checked:
            self.is_frame = True
            self.valueLabel.setText("Go to frame [0, %s]:" % self.frame_count)
            self.valueEdit.setPlaceholderText("Frame number...")
            if not self.user_edited and self.memorized_pos:
                self.valueEdit.setText(unicode(self.memorized_pos[0]))
                self.valueEdit.selectAll()
        else:
            self.is_frame = False
            self.valueLabel.setText("Go to time [0, %s] sec:" % self.video_duration)
            self.valueEdit.setPlaceholderText("Float time value...")
            if not self.user_edited and self.memorized_pos:
                self.valueEdit.setText(unicode(self.memorized_pos[1]))
                self.valueEdit.selectAll()

    def accept(self):
        """
        Called automatically when OK button is pressed to close dialog
        """
        value = self.valueEdit.text()

        # if no value given
        if value:
            try:
                value = float(value)
            except ValueError:
                logger.debug("Given value is not a number.")
                QApplication.beep()
                return

            if self.is_frame:
                if 0 <= value <= self.frame_count:
                    frame_duration = 1000.0 / self.fps
                    new_time = value * frame_duration
                else:
                    logger.debug("Given frame value is out of frame range [0, %s]", self.frame_count)
                    QApplication.beep()
                    return
            else:
                if 0 <= value <= self.video_duration:
                    new_time = value * 1000.0
                else:
                    logger.debug("Given time value is out of time range [0, %s]", self.video_duration)
                    QApplication.beep()
                    return

            logger.debug("Going to new time %s", new_time)
            self.newTimeSelected.emit(new_time)

        super(GoToDialog, self).accept()

    @Slot(unicode)
    def textEdited(self, new_text):
        """
        :type new_text: unicode
        """
        self.user_edited = True