# -*- coding: utf-8 -*-

"""
Module with mediaplayer components.
"""

import time
import datetime
import logging
import os

from PySide.QtGui import *
from PySide.QtCore import *
from PySide.phonon import Phonon


logger = logging.getLogger(__name__)
logger.debug('Import ' + __name__)


class VideoPlayer(Phonon.MediaObject):
    """
    Video player component.
    """

    playing = Signal()
    paused = Signal()
    stopped = Signal()
    loading = Signal()
    buffering = Signal()
    errorOccurred = Signal()
    seeking = Signal(int, int)   # emitted after seek is invoked

    error_title = "Error"
    loading_error = "Video source could not be loaded. Check the log file."
    source_error = "Video source could not be loaded. The file does not exist or it has wrong format."
    snapshot_msg = "Snapshot saved to ./data folder"
    snapshot_error_msg = "Unable to take snapshot"

    loading_state_msg = "Video is loading..."
    stopped_state_msg = "Video has been stopped"
    playing_state_msg = "Playing the video..."
    buffering_state_msg = "Buffering video..."
    paused_state_msg = "Video has been paused"
    error_state_msg = "Video error occurred"

    isPlaying = False
    isPaused = False
    isStopped = True
    validMedia = False
    source = None
    newFrame = None

    def __init__(self, parent, path):
        """
        :type parent: tovian.gui.dialogs.mainwindow.MainApp
        :param path: path to file
        :type path: str
        """
        super(VideoPlayer, self).__init__(parent)
        self.playPauseBtn = parent.playPauseBtn
        self.stopBtn = parent.stopBtn
        self.frameRightBtn = parent.frameRightBtn
        self.frameLeftBtn = parent.frameLeftBtn
        self.skipLeftBtn = parent.skipLeftBtn
        self.skipRightBtn = parent.skipRightBtn
        self.perFrameSlider = parent.perFrameSlider
        self.oldPerFrameSeekerValue = parent.perFrameSlider.value()
        self.timeLbl = parent.timeLbl
        self.audioOutput = parent.audioOuptut
        self.fps = parent.video.fps
        self.frameCount = parent.video.frame_count
        self.videoDuration = 1000 * parent.video.duration
        self.statusbar = parent.statusbar
        self.MSG_DURATION = parent.MSG_DURATION
        self.SHORT_MSG_DURATION = parent.SHORT_MSG_DURATION
        self.annotationBuffer = parent.buffer
        self.videoWidget = parent.videoWidget
        self.per_frame_slider_LButton_pressed = False
        # signals
        self.stateChanged.connect(self.playerStateChanged)
        self.playing.connect(self.disablePerFrameSlider)
        self.paused.connect(self.enablePerFrameSlider)
        self.stopped.connect(self.disablePerFrameSlider)
        self.tick.connect(self.videoTimeLabelSynch)
        self.seeking.connect(self.videoTimeLabelSynch)
        # init
        self.playIcon = QIcon(":/icons/icons/media-play.png")
        self.pauseIcon = QIcon(":/icons/icons/media-pause.png")
        self.newFrameTimer = QTimer()
        self.setTickInterval(100)
        self.loadFile(path)
        logger.debug("Media player was initialized")

    def seek(self, newTime):
        """
        Seeks video to new time (position) and emits signal seeked(frame, newTime)
        :param newTime: new time in ms
        :type newTime: float
        """
        timer_was_active = self.newFrameTimer.isActive()
        self.newFrameTimer.stop()

        # reset buffer to new frame
        totalTime = self.totalTime()
        frame_duration = 1000.0 / self.fps
        newTime = 0 if newTime < 0 else totalTime if newTime > totalTime else round(frame_duration * round(float(newTime)/frame_duration))
        frame = int(round(newTime * self.fps / 1000.0))
        self.annotationBuffer.resetBuffer(frame)            # buffer new frames in advance

        # seek video
        super(VideoPlayer, self).seek(int(newTime))
        logger.debug("Seeked to new time '%s', frame: %s" % (newTime, frame))
        self.seeking.emit(newTime, frame)       # emits new frame and new time manually, because seeking is asynchronous

        if timer_was_active:
            self.newFrameTimer.start(1000.0/self.fps)

    @Slot()
    def seekFrameForward(self):
        """
        Seeks video one frame forward
        """
        newTime = round(self.currentTime() + (1000.0 / self.fps))
        if newTime <= self.totalTime():
            self.seek(newTime)
        else:
            QApplication.beep()
        self.resetPerFrameSlider()

    @Slot()
    def seekFrameBackward(self):
        """
        Seeks video one frame backward
        """
        newTime = round(self.currentTime() - (1000.0 / self.fps))
        if newTime >= 0:
            self.seek(newTime)
        else:
            QApplication.beep()
        self.resetPerFrameSlider()

    @Slot()
    def seekSecForward(self):
        """
        Seeks one second forward
        """
        currentTime = self.currentTime()
        totalTime = self.totalTime()

        if currentTime == totalTime:
            QApplication.beep()
        else:
            newTime = currentTime + 1000
            newTime = totalTime if newTime > totalTime else newTime
            self.seek(newTime)
            self.resetPerFrameSlider()

    @Slot()
    def seekSecBackward(self):
        """
        Seeks one frame back
        """
        currentTime = self.currentTime()

        if currentTime == 0:
            QApplication.beep()
        else:
            newTime = currentTime - 1000
            newTime = 0 if newTime < 0 else newTime
            self.seek(newTime)
            self.resetPerFrameSlider()

    def totalTime(self):
        """
        Builtin method returns video length in ms.
        If diff between returned value and value stored in db is grater than 5%, use value stored in db
        There is a problem with returned value, which may differ from real video length => comparison with db value
        :return: total video duration in ms
        :rtype : int
        """
        totalTime = super(VideoPlayer, self).totalTime()
        totalTime = self.videoDuration if abs(totalTime - self.videoDuration) > 0.05 * self.videoDuration else totalTime
        return totalTime

    def loadFile(self, path):
        """
        Prepares and sets MediaPlayer source.
        :param path: path to source
        :type path: str
        """
        if path is None:
            logger.error("Video source is 'None'")
            self.errorOccurred.emit()
            QMessageBox(QMessageBox.Critical, self.error_title, self.loading_error).exec_()
            return

        self.source = path
        mediaSource = Phonon.MediaSource(self.source)

        if mediaSource.type() != Phonon.MediaSource.LocalFile:
            logger.error("Video source '%s' could not be loaded" % path)
            self.errorOccurred.emit()
            QMessageBox(QMessageBox.Critical, self.error_title, self.source_error).exec_()
            return

        self.setCurrentSource(mediaSource)      # create the media
        self.validMedia = True
        logger.debug("Video source was loaded")

    @Slot()
    def playPauseVideo(self):
        """
        Toggle play/pause status
        """
        logger.debug("Play/pause btn clicked")
        if self.validMedia:

            if self.isPlaying:
                logger.debug("Pausing the video")
                self.pause()
            else:
                if self.totalTime() == self.currentTime():
                    logger.debug("Cannot play the video, video is at the end")
                    return

                logger.debug("Trying to play the video")
                self.play()

            # reset default slider position
            self.resetPerFrameSlider()
            self.stopBtn.setEnabled(True)

        else:
            logger.error("Cannot play the video. Given media source is invalid.")

    @Slot()
    def stopVideo(self):
        """
        Stop the player
        """
        if self.validMedia:
            logger.debug("Stopping the video")
            self.stop()
            self.stopBtn.setEnabled(False)

    @Slot()
    def mute(self):
        """
        Toggle audio mute
        """
        mute = not self.audioOutput.isMuted()
        self.audioOutput.setMuted(mute)
        logger.debug("Video is muted: %s" % mute)

    @Slot()
    def volumeUp(self, value=None):
        """
        Increase the volume by $x percent
        :param value: percentage of volume (e.g. 0.1 = 10%)
        :type value: float
        """
        volume = self.audioOutput.volume()
        value = 0.1 if value is None else value
        volume = volume if volume > 0 else 0.01
        newVolume = volume + value*self.audioOutput.volume()
        newVolume = 0 if newVolume < 0 else 1.0 if newVolume > 1.0 else newVolume
        self.audioOutput.setVolume(newVolume)

    @Slot()
    def volumeDown(self, value=None):
        """
        Decrease the volume by $x percent
        :param value: percentage of volume (e.g. 0.1 = 10%)
        :type value: float
        """
        volume = self.audioOutput.volume()
        value = 0.1 if value is None else value
        newVolume = volume - value*self.audioOutput.volume()
        newVolume = 0 if newVolume < 0 else 1.0 if newVolume > 1.0 else newVolume
        self.audioOutput.setVolume(newVolume)

    def resetPerFrameSlider(self):
        """
        Reset slider to its default position
        """
        logger.debug("Called reset per frame slider")
        self.perFrameSlider.blockSignals(True)
        self.perFrameSlider.setValue(0)
        self.perFrameSlider.blockSignals(False)
        self.oldPerFrameSeekerValue = 0

    def enablePerFrameSlider(self):
        """
        Enable perFrameSlider widget to user interaction
        """
        self.perFrameSlider.setEnabled(True)

    def disablePerFrameSlider(self):
        """
        Disable perFrameSlider widget to user interaction
        """
        self.perFrameSlider.setEnabled(False)

    @Slot(Phonon.State, Phonon.State)
    def playerStateChanged(self, newstate, oldstate):
        """
        When player state is changed, this SLOT gets new and previous player state.
        Depending on new state, state signal is emitted (playing, paused, etc.)
        :param newstate: new player state
        :param oldstate: previous player state
        :type newstate: PySide.phonon.Phonon.State
        :type oldstate: PySide.phonon.Phonon.State
        """
        # TODO move every gui element to gui module

        # LOADING
        if newstate == Phonon.LoadingState:
            logger.debug("Player is loading")
            self.statusbar.showMessage(self.loading_state_msg)
            self.loading.emit()

        # STOPPED
        elif newstate == Phonon.StoppedState:
            logger.debug("Player is stopped")
            self.newFrameTimer.stop()

            self.statusbar.showMessage(self.stopped_state_msg, self.MSG_DURATION)
            self.isPlaying = False
            self.isPaused = False
            self.isStopped = True
            self.playPauseBtn.setIcon(self.playIcon)

            self.stopped.emit()

       # PLAYING
        elif newstate == Phonon.PlayingState:
            logger.debug("Player is playing")
            self.newFrameTimer.start(1000.0/self.fps)

            self.statusbar.showMessage(self.playing_state_msg, self.MSG_DURATION)
            self.isPlaying = True
            self.isPaused = False
            self.isStopped = False
            self.playPauseBtn.setIcon(self.pauseIcon)

            self.playing.emit()

        # BUFFERING
        elif newstate == Phonon.BufferingState:
            logger.debug("Player is buffering")
            self.statusbar.showMessage(self.buffering_state_msg, self.MSG_DURATION)
            self.buffering.emit()

        # PAUSED
        elif newstate == Phonon.PausedState:
            logger.debug("Player is paused")
            self.newFrameTimer.stop()

            self.statusbar.showMessage(self.paused_state_msg, self.MSG_DURATION)
            self.isPlaying = False
            self.isPaused = True
            self.isStopped = False
            self.playPauseBtn.setIcon(self.playIcon)

            self.paused.emit()
        # ERROR
        elif newstate == Phonon.ErrorState:
            logger.error("Error type: %s \nMessage: %s" % (self.errorType(), self.errorString()))
            self.newFrameTimer.stop()

            self.statusbar.showMessage(self.error_state_msg)
            self.isStopped = True
            self.isPlaying = False
            self.isPaused = False

            self.errorOccurred.emit()

            QMessageBox(QMessageBox.Critical, self.error_title,
                        "Error type: %s \nMessage: %s" % (self.errorType(), self.errorString())).exec_()

    def getCurrentFrame(self):
        """
        Calculates and returns current frame number
        :rtype : int
        """
        # get current frame number
        frame = int(round(self.currentTime() * self.fps / 1000.0))
        if frame > self.frameCount:
            frame = self.frameCount
        return frame

    def perFrameSeek(self, value):
        """
        Called when perFrame seeker is moved. Method seeks to next/prev frame.
        :type value: int
        """
        logger.debug("Called perframe seek, value: %s" % value)
        # calculate new position (time)
        diff = value - self.oldPerFrameSeekerValue
        fpsDuration = 1000.0 / self.fps
        newTime = round(self.currentTime() + diff * fpsDuration)

        # if the video is on first/last frame, do not change (decrease/increase) the slider value
        frame = round(newTime * self.fps / 1000.0)
        if frame < 0 or frame > self.frameCount:
            self.perFrameSlider.blockSignals(True)
            self.perFrameSlider.setValue(self.oldPerFrameSeekerValue)
            self.perFrameSlider.blockSignals(False)
            return

        self.seek(newTime)
        self.oldPerFrameSeekerValue = value

        # if value has not been changed by mouse
        if not self.per_frame_slider_LButton_pressed:
            # If slider position is less than 5% from beginning or to end of slider, reset its position.
            self.per_frame_slider_LButton_pressed = False
            maximum = self.perFrameSlider.maximum()
            minimum = self.perFrameSlider.minimum()
            value = self.perFrameSlider.value()
            border = 0.05 * maximum      # 5%
            if (maximum - value) <= border or (value - minimum) <= border:
                self.resetPerFrameSlider()

    @Slot()
    def perFrameSliderLMouseReleased(self):
        """
        Called when left mouse button is released on perFrameSlider.
        If slider position is less than 5% from beginning or to end of slider, reset its position.
        """
        self.per_frame_slider_LButton_pressed = False
        maximum = self.perFrameSlider.maximum()
        minimum = self.perFrameSlider.minimum()
        value = self.perFrameSlider.value()
        border = 0.05 * maximum      # 5%
        if (maximum - value) <= border or (value - minimum) <= border:
            self.resetPerFrameSlider()

    def perFrameSliderLMousePressed(self):
        """
        Called when left mouse button is pressed on perFrameSlider.
        """
        self.per_frame_slider_LButton_pressed = True

    def videoTimeLabelSynch(self, currentTime):
        """
        Internal video timer. Called to refresh video time label
        :type currentTime: int
        """
        timeInSec = currentTime / 1000
        ms = round((currentTime/1000.0 - timeInSec) * 1000)
        if ms >= 1000:
            ms = 0
            timeInSec += 1
        hms = time.strftime('%H:%M:%S', time.gmtime(timeInSec))
        self.timeLbl.setText("%s:%03d" % (hms, ms))

    def takeSnapshot(self, filename=None):
        logger.debug("Taking video snapshot")
        if filename is None:
            timelabel = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = "snapshot-%s-%s.jpg" % (self.parent().video.filename, timelabel)

        image = QPixmap.grabWidget(self.videoWidget)
        if not image.isNull():
            path = os.path.join(self.parent().rootPath, 'data', filename)
            if image.save(path):
                logger.debug("Video snapshot successfully saved to location: '%s'" % path)
                self.statusbar.showMessage(self.snapshot_msg, self.SHORT_MSG_DURATION)
            else:
                logger.error("Unable to save video snapshot to location: '%s'" % path)
                self.statusbar.showMessage(self.snapshot_error_msg, self.SHORT_MSG_DURATION)
        else:
            logger.error("Unable to take video snapshot")
            self.statusbar.showMessage(self.snapshot_error_msg, self.SHORT_MSG_DURATION)


class MainVideoSeeker(QSlider):
    """
    Custom implementation of main video seeker
    """

    MIN = 0
    MAX = 500
    PAGE_STEP = 0.05 * MAX      # 5 percent of max
    REFRESH_TIME = 100          # synchronization period

    manuallySet = False
    isSynchronized = False
    temporaryPaused = False

    def __init__(self, parent):
        """
        :param mediaObject: Media object we want to control
        :type mediaObject: VideoPlayer
        :type parent: tovian.gui.GUIForms.MainApp.MainApp
        """
        super(MainVideoSeeker, self).__init__(Qt.Horizontal, parent)
        self.setMinimum(self.MIN)
        self.setMaximum(self.MAX)
        self.setPageStep(self.PAGE_STEP)
        self.setEnabled(False)
        #self.setTracking(True)
        self.setToolTip("Main video seeker")
        # setup player
        self.updateTimer = QTimer()
        self.player = parent.player
        self.player.playing.connect(self.enable)
        self.player.paused.connect(self.updateTimer.stop)
        self.player.stopped.connect(self.disable)
        self.player.seeking.connect(self.synchronize)

        self.updateTimer.timeout.connect(self.synchronize)
        self.valueChanged.connect(self._seekToPosition)

    @Slot(int)
    def _seekToPosition(self, value=None):
        """
        When slider value is changed, seek video to new position
        :type value: int
        """
        # when value is manually changed (programmatically), don't seek (ignore) !!!
        if self.manuallySet:
            self.manuallySet = False
            return

        value = self.value() if value is None else value
        newTime = int(round((float(self.player.totalTime()) / self.maximum()) * value))

        self.isSynchronized = True                      # to prevent automatic synchronization we don't need
        self.player.seek(newTime)                       # seeked signal triggers synchronization
        self.player.resetPerFrameSlider()               # set default position of per frame slider

    def mousePressEvent(self, event):
        """
        Implemented mouse direct jump
        :type event: PySide.QtGui.QMouseEvent
        """
        # if self.player.isPlaying:
        #     self.player.pause()        # pause playing to prevent "seeking oscillations"
        #     self.temporaryPaused = True

        # it needs to be called parent method, but
        # slider value changed event needs to be ignored because of custom implementation value change event
        self.manuallySet = True                         # set to suppress seek
        super(MainVideoSeeker, self).mousePressEvent(event)
        self.manuallySet = False

        # custom implementation of slider value change -> where user clicks, seek to that position
        if event.button() == Qt.LeftButton:
            newValue = self.minimum() + ((self.maximum()-self.minimum()) * event.x()) / self.width()
            self.setValue(newValue)
            event.accept()

    def mouseReleaseEvent(self, event):
        """
        Continue with playing....
        :type event: PySide.QtGui.QMouseEvent
        """
        super(MainVideoSeeker, self).mouseReleaseEvent(event)
        # if self.temporaryPaused:
        #     self.player.play()
        #     self.temporaryPaused = False

    @Slot(int, int)
    def synchronize(self, currentTime=None, frame=None):
        """
        Method is called automatically by timer event to synchronize slider position with current video time
        Or method is called when video is seeked to new time position.
        :type currentTime: int
        :type frame: int
        """
        # when user seeks video using seeker,
        # slider value is synchronized first and then called seek method => called synchronize
        # no need to synchronize if video has been seeked by slider event
        if self.isSynchronized:
            self.isSynchronized = False
            return

        # common synchronization from updateTimer - synchronize slider position with current video time
        currentTime = self.player.currentTime() if currentTime is None else currentTime
        totalTime = self.player.totalTime()
        maximum = self.maximum()

        if currentTime == 0:
            newValue = 0
        else:
            newValue = round((float(currentTime) / totalTime) * maximum)

        # flag to suppress value changed event => do not seek to new position
        self.manuallySet = True
        self.setValue(newValue)

    @Slot()
    def enable(self):
        """
        Enable slider
        """
        self.updateTimer.start(self.REFRESH_TIME)       # start slider position refreshing
        self.setEnabled(True)

    @Slot()
    def disable(self):
        """
        Disable slider
        """
        self.updateTimer.stop()                         # stop slider position refreshing
        self.setEnabled(False)
