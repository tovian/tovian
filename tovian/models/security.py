# -*- coding: utf-8 -*-

"""
    Security tools
"""

__version__ = "$Id: security.py 203 2013-09-23 08:11:27Z campr $"


import bcrypt
import logging


logger = logging.getLogger(__name__)
logger.debug('Import ' + __name__)


def hash_password(password):
    """
    Returns hash of given password
    """
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password, salt)

def match_password(password, password_hash):
    """
    Matches password and hash
    """
    match = bcrypt.hashpw(password, password_hash) == password_hash

    if not match:
        logger.info('Password match failed')

    return match