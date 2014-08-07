# -*- coding: utf-8 -*-

"""
Application main launcher.
"""

import logging
import urllib
import json
import os

from PySide.QtGui import *
from PySide.QtCore import Slot, Signal, QObject, Qt

from .. import models
from .dialogs.videoselect import UserVideoSelection
from .dialogs.login import UserLoginForm
from .dialogs.mainwindow import MainApp
from .dialogs.download import DownloadDialog


logger = logging.getLogger(__name__)
logger.debug('Import ' + __name__)


class MyApplication(QObject):
    """
    Application main launcher.
    """

    error_title = u"Error"
    critical_error_title = u"Critical error"
    server_error = u"Unable to connect to the server:<br \>URL: %s<br \>Error code: %s"
    connection_error = u"Connection to the server cannot be made. Check if you are connected to the internet."

    error = Signal(unicode)
    criticalError = Signal(unicode)

    def __init__(self, rootPath):
        """
        :param rootPath: project root path
        :type rootPath: str
        """
        super(MyApplication, self).__init__()
        self.rootPath = rootPath
        self.user = None
        self.video = None

        self.error.connect(self.displayError)
        self.criticalError.connect(self.displayCriticalError)

        # Opens login form
        self.loginInstance = UserLoginForm()
        self.loginInstance.logged.connect(self.loadUser)
        self.loginInstance.logged.connect(self.logUserLogin)
        self.loginInstance.show()

        logger.debug("Application initialized, Login dialog opened")

    @Slot(models.entity.Annotator)
    def loadUser(self, user):
        """
        Slot for successfully user login. Invokes video selection dialog.
        :type user: tovian.models.entity.Annotator
        """
        logger.debug("Logged user loaded from login dialog")
        self.user = user
        self.openVideoSelection()

    def openVideoSelection(self):
        """
        Opens available video list when user is logged.
        """
        logger.debug("Opening video selection dialog")
        self.vidSelectInstance = UserVideoSelection(self.user, self.rootPath)
        self.vidSelectInstance.videoSelected.connect(self.videoSelected)        # when video is selected
        self.vidSelectInstance.videoSelected.connect(self.logSelectedVideo)
        self.vidSelectInstance.show()

    @Slot(models.entity.Video, int)
    def videoSelected(self, video, fileStatus):
        """
        Loads video object and file status and opens UI.
        :type fileStatus: int
        :type video: tovian.models.entity.Video
        """
        self.video = video

        if fileStatus == 1:
            logger.debug("Selected video is loaded. Opening main app...")
            self.openUI()

        elif fileStatus == 0:
            logger.info("Selected video needs to be downloaded")

            # some problem
            download_status = self.initFileDownloading()
            if not download_status:
                logger.warning("Downloading initialization failed. Reopening video selection.")
                self.downloadFailed()
        else:
            raise ValueError("Loaded video has status 'unavailable'")

    def initFileDownloading(self):
        """
        Tries to download video file from server.
        :return: errors
        :rtype : bool
        """
        # is file available ?
        try:
            connection = urllib.urlopen(self.video.url_download)
            code = connection.getcode()
            connection.close()
        except IOError:
            logger.exception("Connection to the server cannot be made")
            self.error.emit(self.connection_error)
            return False

        # file is unavailable
        if not code == 200:
            logger.error("Unable to download the file. Server returned code: %s", code)
            self.error.emit(self.server_error % (self.video.url_download, code))
            return False

        self.downloadDialog = DownloadDialog(self.video.url_download, self.video.filename, self.rootPath, self.user)
        self.downloadDialog.downloadHasFinished.connect(self.downloadFinished)
        self.downloadDialog.downloadHasFailed.connect(self.downloadFailed)
        self.downloadDialog.show()

        return True

    @Slot()
    def downloadFailed(self):
        """
        Called when video file downloading has failed.
        """
        logger.error("Downloading has failed. Reopening video selection dialog...")

        self.video = None
        self.openVideoSelection()

    @Slot()
    def downloadFinished(self):
        """
        Called when video file downloading has finished. Then main UI opening is invoked.
        """
        logger.debug("Downloading has finished successfully. ")
        self.openUI()

    def openUI(self):
        """
        Opens main application
        """
        logger.debug("************ Opening main GUI ********************")
        self.mainAppInstance = MainApp(self.user, self.video, self.rootPath)
        self.mainAppInstance.show()

    @Slot(unicode)
    def displayError(self, text):
        QMessageBox(QMessageBox.Critical, self.error_title, text).exec_()

    @Slot(unicode)
    def displayCriticalError(self, text):
        QMessageBox(QMessageBox.Critical, self.critical_error_title, text).exec_()
        self.close()

    @Slot(models.entity.Video, int)
    def logSelectedVideo(self, video, fileStatus):
        """
        When user selects a video, log activity to database
        :type video: tovian.models.entity.Video
        :type fileStatus: int
        """
        logger.debug("Logging selected video to database")
        models.repository.logs.insert('gui.video_select',
                                      value={'video_id': video.id, 'video_filename': video.filename},
                                      annotator_id=self.user.id)

    @Slot(models.entity.Annotator)
    def logUserLogin(self, user):
        """
        Log user login activity to database.
        :type user: tovian.models.entity.Annotator
        """
        pathToVersionFile = os.path.join(self.rootPath, 'data', 'version.json')
        try:
            with open(pathToVersionFile) as f:
                versionData = json.loads(f.read())
        except IOError:
            logger.error("Unable to open data/version.json")
            models.repository.logs.insert('gui.exception.version_file_error',
                                          "Unable to open data/version.json",
                                          annotator_id=user.id)
        else:
            try:
                revision = versionData['version']
            except KeyError:
                logger.error("Key 'version' cannot be found in data/version.json")
                models.repository.logs.insert('gui.exception.version_file_error',
                                              "Key 'version' cannot be found in data/version.json",
                                              annotator_id=user.id)
            else:
                logger.debug("Logging user logged activity to database")
                models.repository.logs.insert('gui.login', value={'revision': revision}, annotator_id=user.id)
