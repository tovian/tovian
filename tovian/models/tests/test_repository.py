# -*- coding: utf-8 -*-

import unittest

import os
import tovian.log as log


root_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..')
log.setup_logging(os.path.join(root_dir, 'data', 'log_testing.json'), log_dir=os.path.join(root_dir, 'log'))

import tovian.config as config
import tovian.models as models

import tovian.models.tests.fixtures as fixtures


class RepositoryTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config.load(os.path.join(root_dir, 'config.ini'))

        models.database.db.open_from_config(config.config, 'testing')
        models.database.db.recreate_tables()

        models.database.db.session.add_all(fixtures.create_fixtures())
        models.database.db.session.commit()

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @classmethod
    def tearDownClass(cls):
        pass


    def test_001a_annotators_get_all_enabled(self):
        self.assertEqual(len(models.repository.annotators.get_all_enabled()), 3)

    def test_001b_annotators_get_one_enabled_by_name(self):
        self.assertIsNotNone(models.repository.annotators.get_one_enabled_by_name(u"Pavel Campr"))
        self.assertIsNone(models.repository.annotators.get_one_enabled_by_name(u"foo"))

    def test_001c_annotators_get_one_enabled_by_name_and_password(self):
        self.assertIsNotNone(models.repository.annotators.get_one_enabled_by_name_and_password(u"Pavel Campr", u"pavel123"))
        self.assertIsNone(models.repository.annotators.get_one_enabled_by_name_and_password(u"Test Foo", u"foo123")) # is not enabled
        self.assertIsNone(models.repository.annotators.get_one_enabled_by_name_and_password(u"Pavel Campr", u"foo"))
        self.assertIsNone(models.repository.annotators.get_one_enabled_by_name_and_password(u"foo", u"foo"))

    def test_001d_annotators_get_one_enabled_by_email(self):
        self.assertIsNotNone(models.repository.annotators.get_one_enabled_by_email(u"campr@kky.zcu.cz"))
        self.assertIsNone(models.repository.annotators.get_one_enabled_by_email(u"foo"))

    def test_001e_annotators_get_one_enabled_by_email_and_password(self):
        self.assertIsNotNone(models.repository.annotators.get_one_enabled_by_email_and_password(u"campr@kky.zcu.cz", u"pavel123"))
        self.assertIsNone(models.repository.annotators.get_one_enabled_by_email_and_password(u"foo@abc.cz", u"foo123")) # is not enabled
        self.assertIsNone(models.repository.annotators.get_one_enabled_by_email_and_password(u"campr@kky.zcu.cz", u"foo"))
        self.assertIsNone(models.repository.annotators.get_one_enabled_by_email_and_password(u"foo", u"foo"))

    def test_001f_annotators_get_one(self):
        a1 = models.repository.annotators.get_one(u"campr@kky.zcu.cz")
        a2 = models.repository.annotators.get_one(u"Pavel Campr")
        a3 = models.repository.annotators.get_one(2)
        a4 = models.repository.annotators.get_one("2")
        a5 = models.repository.annotators.get_one(u"2")

        self.assertEqual(a1.id, a2.id)
        self.assertEqual(a1.id, a3.id)
        self.assertEqual(a1.id, a4.id)
        self.assertEqual(a1.id, a5.id)


    def test_002a_annotation_attribute_get_one_by_name(self):
        self.assertIsNotNone(models.repository.annotation_attributes.get_one_by_name(u"position_rectangle"))
        self.assertIsNone(models.repository.annotation_attributes.get_one_by_name(u"not_existing_foo"))

    def test_002b__annotation_attribute_get_one(self):
        a = models.repository.annotation_attributes.get_one_by_id(1)

        a1 = models.repository.annotation_attributes.get_one(u"position_rectangle")
        a2 = models.repository.annotation_attributes.get_one(1)
        a3 = models.repository.annotation_attributes.get_one("1")
        a4 = models.repository.annotation_attributes.get_one(u"1")

        self.assertEqual(a.id, a1.id)
        self.assertEqual(a.id, a2.id)
        self.assertEqual(a.id, a3.id)
        self.assertEqual(a.id, a4.id)


    def test_003a_videos_get_one(self):
        v1 = models.repository.videos.get_one(u"Test Football 1")
        v2 = models.repository.videos.get_one(u"test_football.mp4")
        v3 = models.repository.videos.get_one(1)
        v4 = models.repository.videos.get_one("1")
        v5 = models.repository.videos.get_one(u"1")

        self.assertEqual(v1.id, v2.id)
        self.assertEqual(v1.id, v3.id)
        self.assertEqual(v1.id, v4.id)
        self.assertEqual(v1.id, v5.id)


if __name__ == '__main__':
    unittest.main()
