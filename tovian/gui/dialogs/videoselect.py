# -*- coding: utf-8 -*-

"""
Main user video-selection form.
"""

import os
import urllib
import logging

from PySide.QtGui import *
from PySide.QtCore import *

from tovian.gui.forms import videoselectform
import tovian.models as models


logger = logging.getLogger(__name__)
logger.debug('Import ' + __name__)


class UserVideoSelection(QDialog, videoselectform.Ui_VideoSelection):
    """
    Video selection dialog. Methods tests, if every video file is present on the disk.
    If not, method checks availability on the server. Video availability status is displayed to user in video table.
    """

    available_yes_msg = u"Video is downloaded and ready to annotation"
    available_download_msg = u"Video is not downloaded, but is available on the server to download"
    available_no_msg = u"Video is not downloaded and is not available on the server!"
    not_active_msg = u"Not Active"
    active_msg = u"Active"
    videos_not_found_warning = u"No videos were found for annotation"
    video_unavailable = u"Selected video is unavailable"

    load_video_error_msg = u"Unable to load videos to annotate from database. Check your internet connection."
    error_title = u"Error"
    critical_error_title = u"Critical error"
    select_video_text = u"Select a video:"
    loading_videos_text = u"Loading videos..."

    videoSelected = Signal(models.entity.Video, int)        # selected video flag (signal)
    loadVideos = Signal()
    error = Signal(unicode)
    criticalError = Signal(unicode)

    def __init__(self, user, rootPath):
        """
        :param user: object with logged user
        :param rootPath: project root path
        :type user: tovian.models.entity.Annotator
        :type rootPath: str
        """
        super(UserVideoSelection, self).__init__()

        self.user = user
        self.video = None
        self.rootPath = rootPath
        self.videos = []
        self.status_list = []            # to store video file status (on disk, on server, unavailable)

        self.setupUi(self)
        self.videoTable.cellDoubleClicked.connect(self.accept)
        self.loadVideos.connect(self.displayVideos, Qt.QueuedConnection)
        self.error.connect(self.displayError)
        self.criticalError.connect(self.displayCriticalError)

        self.selectVideoLbl.setText(self.loading_videos_text)
        QTimer.singleShot(0, self.loadVideos.emit)                  # queued calling
        logger.debug("Video selection dialog initialized")

    def setupUi(self, parent):
        """
        :type parent: PySide.QtGui.QWidget
        """
        super(UserVideoSelection, self).setupUi(parent)
        self.setWindowFlags(self.windowFlags() ^ Qt.WindowContextHelpButtonHint)
        self.userNameLbl.setText(self.user.email)
        self.warningLbl.setVisible(False)
        self.infoIcon.setVisible(False)
        # adjust table header size
        header = self.videoTable.horizontalHeader()
        header.setResizeMode(0, QHeaderView.Interactive)
        header.setResizeMode(1, QHeaderView.Stretch)
        header.setResizeMode(2, QHeaderView.ResizeToContents)
        header.setResizeMode(3, QHeaderView.ResizeToContents)
        self.videoTable.setColumnWidth(0, 200)
        self.videoTable.verticalHeader().setResizeMode(QHeaderView.ResizeToContents)        # word wrapping
        # icons init
        icon_size = QSize(20, 20)
        self.available_yes_icon = QPixmap(":/icons/icons/tick.png").scaled(icon_size, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        self.available_download_icon = QPixmap(":/icons/icons/cross.png").scaled(icon_size, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        self.available_no_icon = QPixmap(":/icons/icons/warning.png").scaled(icon_size, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        self.active_no_icon = QPixmap(":/icons/icons/cross.png").scaled(icon_size, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        self.active_yes_icon = QPixmap(":/icons/icons/tick.png").scaled(icon_size, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

    def displayVideos(self):
        """
        Fills the table with videos to annotate.
        For each video method checks, if video is available on the disk (server).
        """
        try:
            self.videos = self.user.videos_to_annotate()
        except Exception:
            logger.exception("Unable to load videos to annotate from database")
            models.repository.logs.insert('gui.exception.videos_loading_error',
                                          "Unable to load videos to annotate from database",
                                          annotator_id=self.user.id)
            self.criticalError.emit(self.load_video_error_msg)
            return

        self.selectVideoLbl.setText(self.select_video_text)
        if not self.videos:
            logger.debug("No videos were found, list from db is empty or None")
            self.infoIcon.setVisible(True)
            self.warningLbl.setVisible(True)
            self.warningLbl.setText(self.videos_not_found_warning)
            return

        logger.debug("Loading videos to table")
        self.videoTable.setRowCount(len(self.videos))         # 10 lines is a minimum

        # fill the table
        i = 0
        for video in self.videos:
            active_icon_lbl = QLabel()
            active_icon_lbl.setAlignment(Qt.AlignCenter)
            downloaded_icon_lbl = QLabel()
            downloaded_icon_lbl.setAlignment(Qt.AlignCenter)

            # is finished ?
            if video.is_finished:
                active_icon_lbl.setPixmap(self.active_no_icon)
                active_icon_lbl.setToolTip(self.not_active_msg)
            else:
                active_icon_lbl.setPixmap(self.active_yes_icon)
                active_icon_lbl.setToolTip(self.active_msg)

            # is ready ?
            video_file_status = self.getVideoFileStatus(video)
            if video_file_status['status'] == 1:
                downloaded_icon_lbl.setPixmap(self.available_yes_icon)
                downloaded_icon_lbl.setToolTip(self.available_yes_msg)
            elif video_file_status['status'] == 0:
                downloaded_icon_lbl.setPixmap(self.available_download_icon)
                downloaded_icon_lbl.setToolTip(self.available_download_msg)
            else:
                downloaded_icon_lbl.setPixmap(self.available_no_icon)
                error = "\nError code: " + str(video_file_status['code'])
                downloaded_icon_lbl.setToolTip(self.available_no_msg + error)

            self.status_list.append(video_file_status['status'])

            # add items to table
            self.videoTable.setItem(i, 0, QTableWidgetItem(video.name))
            self.videoTable.setItem(i, 1, QTableWidgetItem(video.public_comment))
            self.videoTable.setCellWidget(i, 2, active_icon_lbl)
            self.videoTable.setCellWidget(i, 3, downloaded_icon_lbl)
            i += 1

        self.videoTable.selectRow(0)
        logger.debug("Videos have been loaded to table")

    def getVideoFileStatus(self, video):
        """
        Returns video file available state.
        If video is download on disk, return 1.
        If video is not downloaded on disk, but is available on the server, return 0.
        If video is not downloaded on disk and is not available on the server, return -1.
        :type video: tovian.models.entity.Video
        :return: dict (status=, code=)
        :rtype: dict
        """
        try:
            path = os.path.join(self.rootPath, 'data', 'video', video.filename)
            exists = os.path.isfile(path)       # exists in .../data/video
        except OSError:
            logger.exception("Error when checking video file availability on the disk")
            exists = False

        if exists:
            logger.debug("Video file '%s' is present on the disk", video.filename)
            return dict(status=1, code=None)

        # checks if the file is available on the server
        logger.debug("Video file '%s' is not present on the disk. Trying to connect to download server...", video.filename)
        try:
            videoUrl = urllib.urlopen(video.url_download)
            code = videoUrl.getcode()
            videoUrl.close()
        except IOError:
            logger.error("Connection to the server cannot be made")
            return dict(status=-1, code=code)

        if code == 200:
            logger.debug("Video file '%s' is ready to be downloaded if necessary", video.filename)
            return dict(status=0, code=code)
        else:
            logger.debug("Video file '%s' cannot be downloaded, error code: %s", video.filename, code)
            return dict(status=-1, code=code)

    @Slot()
    def accept(self):
        if self.videos:
            index = self.videoTable.currentRow()
            try:
                video = self.videos[index]
            except IndexError:
                logger.exception("Current table index and video index mismatch")
                models.repository.logs.insert('gui.exception.video_loading_from_table_error',
                                              "Current table index and video index mismatch",
                                              annotator_id=self.user.id)
            else:
                fileStatus = self.status_list[index]
                if fileStatus == -1:
                    self.infoIcon.setVisible(True)
                    self.warningLbl.setVisible(True)
                    self.warningLbl.setText(self.video_unavailable)
                    self.videoTable.setFocus()

                    logger.debug("Selected video is unavailable right now")
                    QApplication.beep()
                else:
                    logger.debug("Valid video selected")
                    super(UserVideoSelection, self).accept()
                    self.videoSelected.emit(video, fileStatus)

        else:
            logger.debug("Cannot accept dialog, no videos found")
            QApplication.beep()

    @Slot(unicode)
    def displayError(self, text):
        QMessageBox(QMessageBox.Critical, self.error_title, text).exec_()

    @Slot(unicode)
    def displayCriticalError(self, text):
        QMessageBox(QMessageBox.Critical, self.critical_error_title, text).exec_()
        self.close()




