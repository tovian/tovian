# -*- coding: utf-8 -*-

"""
User login dialog class.
"""

import logging
import ConfigParser
import re

from PySide.QtGui import *
from PySide.QtCore import *

from ..forms import loginform
from tovian.config import config
import tovian.models as models


logger = logging.getLogger(__name__)
logger.debug('Import ' + __name__)


class UserLoginForm(QDialog, loginform.Ui_LoginForm):
    """
    User login dialog. Dialog loads from config.ini file database url.
    """

    enter_username = u"Enter the username"
    enter_password = u"Enter the password"
    invalid_login = u"Invalid username or password"

    error_title = u"Error"
    critical_error_title = u"Critical error"
    db_loading_error = u"Error when connecting to the database. Check the log file."
    config_not_found_msg = u"Key not found in config.ini. Create new config file from config.ini.dist"

    logged = Signal(models.entity.Annotator)
    error = Signal(unicode)
    criticalError = Signal(unicode)

    def __init__(self):
        super(UserLoginForm, self).__init__()

        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() ^ Qt.WindowContextHelpButtonHint)

        self.error.connect(self.displayError)
        self.criticalError.connect(self.displayCriticalError)

        # setup UI
        self.setFixedWidth(460)
        self.setFixedHeight(185)
        self.usernameEdit.setFocus()
        self.infoIcon.setVisible(False)
        self.warningLbl.setVisible(False)
        self.serverEdit.setEnabled(False)

        try:
            dbURL = config.get('DEFAULT', 'database.url')
        except ConfigParser.NoOptionError:
            logger.exception("Unable to find key 'database.url' under group 'DEFAULT' in config file")
            self.criticalError.emit(self.config_not_found_msg)
            models.repository.logs.insert('gui.exception.config_file_error',
                                          "Unable to find key 'database.url' under group 'DEFAULT' in config file",
                                          annotator_id=self.user.id)
        else:
            self.serverEdit.setText(dbURL)              # display db URL

            try:
                default_user = config.get('DEFAULT', 'annotator.username')
                default_pass = config.get('DEFAULT', 'annotator.password')
            except ConfigParser.NoOptionError:
                logger.warning("Warning, annotator.username or annotator.password key not found in config.ini")
            else:
                if default_user:
                    self.usernameEdit.setText(default_user.decode("UTF-8"))
                if default_pass:
                    self.passwordEdit.setText(default_pass.decode("UTF-8"))

            logger.debug("Login dialog initialized")

    def findUser(self, name, password):
        """
        Searches the database for annotator by name or email
        :type password: unicode
        :type name: unicode
        :rtype: tovian.models.entity.Annotator or None
        """

        try:
            if re.match(r"^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$", name):
                logger.debug("Trying to find user by email in database...")
                user = models.repository.annotators.get_one_enabled_by_email_and_password(name, password)
            else:
                logger.debug("Trying to find user by name in database...")
                user = models.repository.annotators.get_one_enabled_by_name_and_password(name, password)

        except Exception:
            user = None
            logger.exception("Error when loading user from database")
            models.repository.logs.insert('gui.exception.user_login_error',
                                          "Error when loading user from database",
                                          annotator_id=self.user.id)
            self.error.emit(self.db_loading_error)

        return user

    @Slot()
    def accept(self):
        """
        When username and password are not empty, login method is called when OK button is pressed.
        """
        logger.debug("Login dialog accepted, processing login information")

        self.infoIcon.setVisible(True)
        self.warningLbl.setVisible(True)

        name = self.usernameEdit.text()
        password = self.passwordEdit.text()

        # username is empty
        if not name:
            logger.info("Username name field is empty")
            self.warningLbl.setText(self.enter_username)
            self.usernameEdit.setFocus()
            return
        # password is empty
        if not password:
            logger.info("Password name field is empty")
            self.warningLbl.setText(self.enter_password)
            self.passwordEdit.setFocus()
            return

        default_cursor = self.cursor()
        self.setCursor(Qt.WaitCursor)

        user = self.findUser(name, password)        # get user from database
        if user:
            super(UserLoginForm, self).accept()     # set result code to accept

            logger.debug("Found user %s", user.email)
            self.logged.emit(user)

        else:
            self.setCursor(default_cursor)
            self.infoIcon.setVisible(True)
            self.warningLbl.setVisible(True)
            self.warningLbl.setText(self.invalid_login)

            logger.info("Username name or password is invalid")

    @Slot(unicode)
    def displayError(self, text):
        QMessageBox(QMessageBox.Critical, self.error_title, text).exec_()

    @Slot(unicode)
    def displayCriticalError(self, text):
        QMessageBox(QMessageBox.Critical, self.critical_error_title, text).exec_()
        self.close()