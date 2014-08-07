# -*- coding: utf-8 -*-

"""
    Version management.
"""

import os
import logging
import json


logger = logging.getLogger(__name__)
logger.debug('Import ' + __name__)


def version(root_dir):
    try:
        with open(os.path.join(root_dir, 'data', 'version.json')) as fr:
            version_data = json.loads(fr.read())
        version_info = ' (%s, %s, %s)' % (version_data['version'], version_data['revision'], version_data['build_date'])
    except:
        version_data = {}
        version_info = ''

    return version_data, version_info