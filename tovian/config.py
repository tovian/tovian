# -*- coding: utf-8 -*-

"""
    Configuration management.
    Configuration is read (by default) from "config.ini", which is a local (not versioned) configuration file.
    If this file is not present, default "config.ini.dist" is used.
"""

import ConfigParser
import os
import sys
import logging


logger = logging.getLogger(__name__)
logger.debug('Import ' + __name__)

config = ConfigParser.ConfigParser()


def load(filename = None, fallback_to_dist = True):
    if not filename:
        # use default location of config.ini
        root_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
        filename = os.path.join(root_dir, 'config.ini')

    if fallback_to_dist and not os.path.exists(filename):
        logger.debug('Configuration file not found (%s), trying to use .dist version.' % (filename))
        filename += '.dist'

    if not os.path.exists(filename):
        raise Exception('Configuration file not found: %s' % (filename))

    config.read(filename)

    logger.debug('Configuration file (%s) read.' % (filename))