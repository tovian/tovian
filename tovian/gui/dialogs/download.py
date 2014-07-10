# -*- coding: utf-8 -*-

"""
User dialog when downloading a file. Dialog shows downloading progress.
"""

__version__ = "$Id: download.py 347 2013-12-10 15:41:12Z herbig $"

import os
import logging

from PySide.QtGui import *
from PySide.QtCore import *

from ..forms.downloadform import Ui_DownloadDialog
from ..components.downloader import Downloader
from tovian import models


logger = logging.getLogger(__name__)
logger.debug('Import ' + __name__)


class DownloadDialog(QDialog, Ui_DownloadDialog):
    """
    Dialog for downloading. It shows downloading progress.
    """

    window_title = u"Downloading file"
    error_title = u"Error"
    critical_error_title = u"Critical error"
    save_path_error_msg = u"Unable to create save directory before downloading"

    downloadHasFinished = Signal()
    downloadHasFailed = Signal()
    endingDownload = Signal()
    invokeDownload = Signal()

    error = Signal(unicode)
    criticalError = Signal(unicode)

    def __init__(self, url, filename, rootPath, user):
        """
        :type url: str
        :type filename: str
        :type rootPath: str
        """
        super(DownloadDialog, self).__init__()

        self.refresh_period = 200
        self.total_size = 0
        self.downloaded = 0
        self.downloaded_prev = 0
        self.percent = 0
        self.user = user

        self.setupUi(self)
        self.setWindowTitle("%s '%s'" % (self.window_title, filename))
        self.setWindowFlags(self.windowFlags() ^ Qt.WindowContextHelpButtonHint)

        self.invokeDownload.connect(self.startDownloading)
        self.error.connect(self.displayError)
        self.criticalError.connect(self.displayCriticalError)

        # init
        self.url = url
        self.filename = filename
        self.rootPath = rootPath
        self.downloader_worker = Downloader(self.user.id, self)

        # dialog refresh
        self.timer = QTimer()
        self.timer.timeout.connect(self.updateUi)               # update download progress
        self.timer.start(self.refresh_period)

        # downloader signals
        self.downloader_worker.finished.connect(self.downloadedSuccessfully)
        self.downloader_worker.failed.connect(self.downloadingError)

        QTimer.singleShot(0, self.invokeDownload.emit)          # when dialog is fully loaded, invoke downloading
        logger.debug("Initialized download dialog")

    @Slot()
    def startDownloading(self):
        """
        Initializes and starts the download.
        """
        logger.debug("Checking save path, starting downloader worker")

        savePath = os.path.join(self.rootPath, 'data', 'video')
        if not os.path.isdir(savePath):
            logger.debug("Save folder doesn't exist, trying to create save folder")
            try:
                os.makedirs(savePath)
            except OSError:
                logger.exception("Failed to create save directory before downloading")
                models.repository.logs.insert('gui.exception.download_folder_error',
                                              "Failed to create save directory before downloading",
                                              annotator_id=self.user.id)
                self.criticalError.emit(self.save_path_error_msg)
                return

        filePath = os.path.join(savePath, self.filename)
        self.downloader_worker.start(self.url, filePath)

    @Slot()
    def updateUi(self):
        """
        Periodically called to update downloading status on dialog.
        """
        self.downloaded = self.downloader_worker.downloaded
        self.total_size = self.downloader_worker.total_size
        self.percent = int(float(self.downloaded)/self.total_size*100) if self.downloaded > 0 else 0
        self.speed = (self.downloaded - self.downloaded_prev) * (1000.0 / self.refresh_period)
        self.downloaded_prev = self.downloaded

        # format values to B/kB/Mb etc.
        if self.total_size > 10**9:
            totalSizeStr = "%0.2f GB" % (self.total_size/10.0**9)
        elif self.total_size > 10**6:
            totalSizeStr = "%0.2f MB" % (self.total_size/10.0**6)
        elif self.total_size > 10**3:
            totalSizeStr = "%0.2f kB" % (self.total_size/10.0**3)
        else:
            totalSizeStr = "%0.0f B" % self.total_size
        if self.speed > 10**6:
            speedStr = "%0.2f MB/s" % (self.speed/10.0**6)
        elif self.speed > 10**3:
            speedStr = "%0.2f kB/s" % (self.speed/10.0**3)
        else:
            speedStr = "%0.0f B/s" % self.speed
        if self.downloaded > 10**9:
            downloadedStr = "%0.2f GB (%s)" % ((self.downloaded/10.0**9), speedStr)
        elif self.downloaded > 10**6:
            downloadedStr = "%0.2f MB (%s)" % ((self.downloaded/10.0**6), speedStr)
        elif self.downloaded > 10**3:
            downloadedStr = "%0.2f kB (%s)" % ((self.downloaded/10.0**3), speedStr)
        else:
            downloadedStr = "%0.0f B (%s)" % (self.downloaded, speedStr)

        self.totalSizeLbl.setText(totalSizeStr)
        self.downloadedLbl.setText(downloadedStr)
        self.progressBar.setValue(self.percent)

    @Slot()
    def downloadedSuccessfully(self):
        """
        Called when downloading is finished.
        """
        self.timer.stop()
        self.accept()

        self.downloadHasFinished.emit()
        logger.debug("Download dialog ends. Status: Successful")

    @Slot(unicode)
    def downloadingError(self, message):
        """
        Called when downloading has failed.
        :param message: error message
        :type message: str
        """
        self.timer.stop()
        self.accept()

        self.error.emit(message)
        logger.debug("Download dialog ends. Status: Failed")

    def reject(self):
        """
        When Cancel is pressed, do not close the dialog.
        """
        logger.debug("Reject called (cancel pressed)")
        self.timer.stop()

        if self.downloader_worker.isAlive():
            logger.debug("Downloader is alive, calling for download interruption.")
            self.downloader_worker.stop()

        super(DownloadDialog, self).reject()

    @Slot(unicode)
    def displayError(self, text):
        QMessageBox(QMessageBox.Critical, self.error_title, text).exec_()
        self.downloadHasFailed.emit()

    @Slot(unicode)
    def displayCriticalError(self, text):
        QMessageBox(QMessageBox.Critical, self.critical_error_title, text).exec_()
        self.reject()
        self.downloadHasFailed.emit()
