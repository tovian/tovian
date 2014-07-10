# -*- coding: utf-8 -*-

__version__ = "$Id: test_config.py 221 2013-09-26 09:59:06Z campr $"


import unittest
import os

import tovian.log as log

root_dir = os.path.join(os.path.dirname(__file__), '..', '..')
log.setup_logging(os.path.join(root_dir, 'data', 'log_testing.json'), log_dir=os.path.join(root_dir, 'log'))

import tovian.config as config


class ConfigTestCase(unittest.TestCase):
    def setUp(self):
        config.load(os.path.join(root_dir, 'config.ini.dist'), False)

    def tearDown(self):
        pass

    def test_001_config(self):
        self.assertEqual(config.config.getboolean('DEFAULT', 'sqlalchemy.engine.echo'), False)
        self.assertEqual(config.config.getboolean('production', 'sqlalchemy.engine.echo'), False)
        self.assertEqual(config.config.getboolean('testing', 'sqlalchemy.engine.echo'), True)


if __name__ == '__main__':
    unittest.main()
