#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Application main launcher.
"""

import logging
import os, sys
import colorama

from tovian import log


logger = logging.getLogger(__name__)
logger.debug('Import ' + __name__)

colorama.init()


environments = {
    'production': {
        'logging_config_file': 'log_production.json',
    },
    'debug': {
        'logging_config_file': 'log_debug.json',
    },
    'debug_db': {
        'logging_config_file': 'log_debug.json',
    },
    'testing': {
        'logging_config_file': 'log_testing.json',
    },
    'admin': {
        'logging_config_file': 'log_production.json',
    },
}


def versiontuple(v):
    """
        converts string like "0.8.1" to tuple (0, 8, 1)
    """
    return tuple(map(int, (v.split("."))))

def check_requirements():
    if sys.version_info < (2, 7) or sys.version_info >= (3, 0):
        raise Exception("must use python 2.7")

    try:
        import bcrypt
    except:
        raise Exception('bcrypt library is missing')

    try:
        import termcolor
    except:
        raise Exception('termcolor library is missing')

    try:
        import colorama
    except:
        raise Exception('colorama library is missing')

    try:
        import sqlalchemy
    except:
        raise Exception('sqlalchemy library is missing')

    if versiontuple(sqlalchemy.__version__) < versiontuple('0.8'):
        raise Exception('sqlalchemy 0.8 or higher is required, current version is %s' % (sqlalchemy.__version__))

    try:
        import MySQLdb
    except:
        raise Exception('MySQLdb library is missing')

    if versiontuple(MySQLdb.__version__) < versiontuple('1.2.4'):
        raise Exception('MySQLdb 1.2.4 or higher is required, current version is %s' % (MySQLdb.__version__))

    try:
        import PySide
    except:
        raise Exception('PySide library is missing')

    if versiontuple(PySide.__version__) < versiontuple('1.2.1'):
        raise Exception('PySide 1.2 or higher is required, current version is %s' % (PySide.__version__))

    try:
        import PySide.phonon
    except:
        raise Exception('PySide.phonon library is missing')


def start(environment='production'):
    # initialize logging before anything else
    root_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
    # root_dir = unicode(root_dir, sys.getfilesystemencoding())
    log_dir = os.path.join(root_dir, 'log')

    if not os.path.isdir(log_dir):
        os.mkdir(log_dir)

    log.setup_logging(os.path.join(root_dir, 'data', environments[environment]['logging_config_file']), log_dir=log_dir)

    # import after logging is initialized
    from tovian import config
    from tovian.gui import launcher
    from tovian import models
    import tovian.version
    import PySide.QtGui
    import json
    import platform

    version_data, version_info = tovian.version.version(root_dir)

    # load configuration
    config.load(os.path.join(root_dir, 'config.ini'))

    # initialize database connection
    models.database.db.open_from_config(config.config, environment)

    # start GUI
    logger.debug("Start GUI, environment = %s" % (environment))

    core = PySide.QtGui.QApplication(sys.argv)
    core.setApplicationName("Tovian")
    myApp = launcher.MyApplication(root_dir)

    # logging
    models.repository.logs.insert('gui.start', {
        'environment': environment,
        'root_dir': root_dir,
        'platform': {'platform': platform.platform(), 'uname': platform.uname()},
        'tovian': version_data
    })

    try:
        core.exec_()
    except Exception, e:
        logger.error("Exception in core.exec_(): "+sys.exc_info()[0])
        models.repository.logs.insert('gui.exception.core.exec_()', sys.exc_info()[0])
        raise e
    finally:
        models.repository.logs.insert('gui.stop', {'db_sql_count': models.database.db.profiler['sql_count']})
        logger.debug("Stop GUI")

        models.database.db.close()


if __name__ == "__main__":
    check_requirements()
    start()