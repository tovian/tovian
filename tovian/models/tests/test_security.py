# -*- coding: utf-8 -*-

__version__ = "$Id: test_security.py 221 2013-09-26 09:59:06Z campr $"


import unittest

import tovian.models.security as security


class SecurityTestCase(unittest.TestCase):
    def test_password_hash(self):
        password = u'password1'
        hash = security.hash_password(password)

        self.assertTrue(security.match_password(password, hash))
        self.assertFalse(security.match_password(u'foo', hash))


if __name__ == '__main__':
    unittest.main()
