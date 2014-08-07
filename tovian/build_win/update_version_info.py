# -*- coding: utf-8 -*-

"""
Updates information in data/version.json:
  date is updated to now
  revision number is extracted by svn or git
"""

import sys
import os
import json
import datetime


def get_revision(dir):
    # try git
    cmd = 'git -C %s log -n 1 | grep "commit"' % (dir)
    revision = os.popen(cmd).read().strip()

    if revision:
        return revision.replace('commit', '').strip()[:10]

    # try svn
    cmd = 'svn info %s | grep "Revision"' % (dir)
    revision = os.popen(cmd).read().strip()

    if revision:
        return 'r'+revision.replace('Revision:', '').strip()

    raise Exception('Cannot get revision (git or svn)')


if __name__ == "__main__":
    version_fn = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'version.json')

    with open(version_fn, 'r') as fr:
        version_data = json.load(fr)

    version_data['revision'] = get_revision('../..')
    version_data['build_date'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(version_fn, 'w') as fw:
        json.dump(version_data, fw, indent=4)

    print version_data