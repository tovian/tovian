# -*- coding: utf-8 -*-

"""
Comment.
"""

import os
import threading
import urllib
import logging

from PySide.QtCore import Signal, QObject
from tovian import models


logger = logging.getLogger(__name__)
logger.debug('Import ' + __name__)


class Downloader(QObject):
    """
    File downloader component. Emits finished() and failed(msg) signals.
    """

    connection_error = u"Connection to the server cannot be made.<br />URL: %s"
    server_error = u"Server has responded with %s code. Check the given URL.<br />URL: %s"
    get_file_size_error = u"Unable to get size of the downloaded file."
    opening_file_error = u"Unable to use the destination:<br />%s<br />Check the access rights."
    writing_file_error = u"Unable to write downloaded data:<br />%s<br />Check the access rights."
    interrupt_msg = u"Downloading has been interrupted."
    file_validation_error = u"The file size is not equal to the expected size. The downloaded file is corrupted."
    unexpected_os_error = u"Unexpected error when writing/renaming downloaded file. Check the log file."

    finished = Signal()
    failed = Signal(unicode)

    def __init__(self, user_id, parent):
        super(Downloader, self).__init__(parent)
        self.downloaded = 0
        self.total_size = 0
        self.buffer_size = 8 * 1024
        self.interrupt = False
        self.thread = None
        self.thread_timeout = 5
        self.user_id = user_id

    def start(self, url, path):
        """
        Starts file downloading from given url to given path.
        :type url: str
        :type path: str
        """
        logger.debug("Initializing downloader thread")
        self.resetVars()                        # class may be reused after error

        self.thread = threading.Thread(target=self.__downloading, args=(url, path))
        self.thread.start()

        logger.debug("Downloading thread has started")

    def resetVars(self):
        """
        Reset variables in case that class runs multiple times
        """
        self.downloaded = 0
        self.total_size = 0
        self.buffer_size = 8 * 1024
        self.interrupt = False

    def __downloading(self, url, path):
        """
        Starts downloading the file.
        :type url: str
        :type path: str
        """
        temp_path = path + '_part'
        continue_ = True
        try:
            connection = urllib.urlopen(url)
        except IOError:
            logger.exception("Connection to %s cannot be made." % temp_path)
            self.failed.emit(self.connection_error % url)
            return

        conn_code = connection.code
        if conn_code != 200:
            logger.error("Server has responded with %s code" % conn_code)
            self.failed.emit(self.server_error % (conn_code, url))
            connection.close()
            return

        logger.debug("Successfully connected to the server.")

        try:
            self.total_size = int(connection.info()['Content-Length'])
        except ValueError:
            logger.error("Unable to get size of the downloaded file.")
            self.failed.emit(self.get_file_size_error)
            connection.close()
            return

        try:
            self.file = open(temp_path, "wb")
        except IOError:
            logger.exception("Unable to use destination path: %s", temp_path)
            models.repository.logs.insert('gui.exception.downloader_save_folder_error',
                                          "Unable to use destination path: %s" % temp_path,
                                          annotator_id=self.user_id)
            self.failed.emit(self.opening_file_error % temp_path)
            connection.close()
            return

        logger.debug("Starting file download from server")

        try:
            while not self.interrupt and continue_:
                data = connection.read(self.buffer_size)
                self.file.write(data)
                self.downloaded += len(data)
                continue_ = data
            self.file.close()
        except IOError:
            logger.exception("Unable to write downloaded data: %s", temp_path)
            models.repository.logs.insert('gui.exception.downloader_write_data_error',
                                          "Unable to write downloaded data: %s" % temp_path,
                                          annotator_id=self.user_id)
            self.failed.emit(self.writing_file_error % temp_path)
            connection.close()
            return

        if self.interrupt:
            logger.debug("Downloading has been interrupted.")
            try:
                os.remove(temp_path)
            except:
                logger.exception("Error when removing temp file")
                models.repository.logs.insert('gui.exception.removing_temp_file_error',
                                              "Error when removing temp file",
                                              annotator_id=self.user_id)
            self.failed.emit(self.interrupt_msg)
            connection.close()
            return

        connection.close()
        logger.debug("File downloaded and connection closed.")

        # when downloading is finished
        try:
            # basic file validation
            fileSize = os.path.getsize(temp_path)

            if self.total_size != fileSize:
                os.remove(temp_path)
                logger.error("The file size is not equal to the expected size")
                self.failed.emit(self.file_validation_error)
                return

            os.rename(temp_path, path)
        except OSError:
            logger.exception("Error when writing/renaming downloaded file.")
            models.repository.logs.insert('gui.exception.downloader_clean_up_error',
                                          "Error when writing/renaming downloaded file.",
                                          annotator_id=self.user_id)
            self.failed.emit(self.unexpected_os_error)
            return

        logger.debug("File has been stored and renamed")
        self.finished.emit()

    def stop(self):
        """
        Interrupts downloading.
        """
        logger.debug("Trying to interrupt the download")
        self.interrupt = True
        self.thread.join(self.thread_timeout)                          # waits 5 sec until thread finishes

    def isAlive(self):
        """
        Return True, if thread is still alive or False if not
        :rtype: bool
        """
        if self.thread is None:
            return False
        else:
            return self.thread.isAlive()



