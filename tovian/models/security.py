# -*- coding: utf-8 -*-

"""
    Security tools
"""

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