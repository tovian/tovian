# -*- coding: utf-8 -*-

"""
    Logging - setup_logging() loads logging configuration from JSON file
"""

import logging
import logging.config
import json
import os
import termcolor


logger = logging.getLogger(__name__)
logger.debug('Import ' + __name__)


class FilterInfo(logging.Filter):
    def filter(self, rec):
        return rec.levelno in (logging.DEBUG, logging.INFO)

class ColorHandler(logging.StreamHandler):
    """
    Logging handler, adds color in console output
    """

    colormap = dict(
        #debug=dict(color='grey', attrs=['bold']),
        info=dict(color='white', attrs=['bold']),
        warn=dict(color='magenta', attrs=['bold']),
        warning=dict(color='magenta', attrs=['bold']),
        error=dict(color='red', on_color='on_white', attrs=['bold']),
        critical=dict(color='red', on_color='on_white', attrs=['bold']),
    )

    def format(self, record):
        msg = self.formatter.format(record)

        if record.levelname.lower() in self.colormap.keys():
            msg = termcolor.colored(msg, **self.colormap[record.levelname.lower()])

        return msg


def replace_in_values(d, find, replace):
    """
    Loops through nested dict, replaces string values in lists
    """
    if type(d)==type({}):
        for k in d:
            if isinstance(d[k], basestring):
                d[k] = d[k].replace(find, replace)
            else:
                replace_in_values(d[k], find, replace)

    return d

def setup_logging(json_config_filepath = 'log_production.json', log_dir = '.'):
    if not os.path.exists(json_config_filepath):
        raise Exception('Logging configuration file not found: %s' % (json_config_filepath))

    with open(json_config_filepath, 'r') as fr:
        config = json.load(fr)

    # set root dir in configuration values
    config = replace_in_values(config, '%ROOTDIR%', log_dir)

    logging.config.dictConfig(config)

    logger.debug('Logging setup: %s was loaded.' % (json_config_filepath))


if __name__ == '__main__':
    # just for testing:
    setup_logging('log_debug.json')
    logger.debug('test d')
    logger.info('test i')
    logger.error('test e')
