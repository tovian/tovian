# -*- coding: utf-8 -*-

import os
import json
import unittest

import tovian.log as log


root_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..')
log.setup_logging(os.path.join(root_dir, 'data', 'log_testing.json'), log_dir=os.path.join(root_dir, 'log'))

import tovian.config as config
import tovian.models as models
import tovian.models.tests.fixtures as fixtures


class EntityTestCase(unittest.TestCase):
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


    def test_001a_annotator_repr(self):
        annotator_pavel = models.repository.annotators.get_one_enabled_by_name(u"Pavel Campr")
        self.assertTrue(str(annotator_pavel).startswith('<Annotator#2('))

        annotator_new = models.entity.Annotator(name=u'ěšč')
        self.assertTrue(str(annotator_new).startswith('<Annotator#None('))

    def test_001b_annotator_relations(self):
        annotator_pavel = models.repository.annotators.get_one_enabled_by_name(u"Pavel Campr")

        self.assertEqual(len(annotator_pavel.slaves), 2)
        self.assertEqual(annotator_pavel.master.name, u"admin")

    def test_001c_annotator_disabled(self):
        annotator_foo = models.repository.annotators.get_one_enabled_by_name(u"Test Foo")
        self.assertIsNone(annotator_foo)

    def test_001d_annotator_password_match(self):
        annotator_pavel = models.repository.annotators.get_one_enabled_by_name(u"Pavel Campr")

        self.assertTrue(annotator_pavel.match_password(u"pavel123"))
        self.assertFalse(annotator_pavel.match_password(u"xxx"))

    def test_001e_annotator_password_set(self):
        annotator_pavel = models.repository.annotators.get_one_enabled_by_name(u"Pavel Campr")

        # exceptions for short passwords
        try:
            annotator_pavel.password = u"1"
        except:
            pass
        else:
            self.fail()

        try:
            annotator_pavel.password = u"pavel123"
        except:
            self.fail()


    def test_001f_annotators_relations(self):
        annotator_pavel = models.repository.annotators.get_one_enabled_by_name(u"Pavel Campr")
        videos_pavel = annotator_pavel.videos

        self.assertEqual(len(videos_pavel), 6)

    def test_001g_annotator_videos_to_annotate(self):
        annotator_pavel = models.repository.annotators.get_one_enabled_by_name(u"Pavel Campr")
        self.assertEqual(len(annotator_pavel.videos_to_annotate()), 5)

        annotator_admin = models.repository.annotators.get_one_enabled_by_name(u"admin")
        videos = annotator_admin.videos_to_annotate()
        self.assertEqual(len(videos), 5)
        self.assertEqual(videos[0].name, u"Test Football 1")

    def test_001h_annotator_video_to_annotate_by_id(self):
        annotator_admin = models.repository.annotators.get_one_enabled_by_name(u"admin")
        self.assertIsNotNone(annotator_admin.video_to_annotate_by_id(1))
        self.assertIsNone(annotator_admin.video_to_annotate_by_id(2))

    def test_001i_annotator_options(self):
        annotator_admin = models.repository.annotators.get_one_enabled_by_name(u"admin")
        self.assertEquals(annotator_admin.get_option(['gui', 'color', 'annotation_object_visual']), 'blue')
        self.assertEquals(annotator_admin.get_option('gui.color.annotation_object_visual'), 'blue')

        try:
            annotator_admin.get_option(['foo'])
        except:
            pass
        else:
            self.fail()

    def test_002a_video_repr(self):
        video_football = models.repository.videos.get_one_by_id(1)
        self.assertTrue(str(video_football).startswith('<Video#1('))

        video_new = models.entity.Video(name=u'ěšč')
        self.assertTrue(str(video_new).startswith('<Video#None('))

    def test_002b_video_annotation_objects_all(self):
        video_football = models.repository.videos.get_one_by_id(1)
        self.assertIsNotNone(video_football)

        aos = video_football.annotation_objects_all()

        self.assertEqual(len(aos), 15)

        # correctly ordered?
        self.assertEqual(aos[0][1:], (0, 12))
        self.assertEqual(aos[1][1:], (0, 30))
        self.assertEqual(aos[2][1:], (31, 123))
        self.assertEqual(aos[3][1:], (124, 325))
        self.assertEqual(aos[4][1:], (139, 337))
        self.assertEqual(aos[5][1:], (246, 292))
        self.assertEqual(aos[6][1:], (322, 632))
        self.assertEqual(aos[7][1:], (382, 549))
        self.assertEqual(aos[8][1:], (550, 550))
        self.assertEqual(aos[9][1:], (627, 627))
        self.assertEqual(aos[10][1:], (633, 635))
        self.assertEqual(aos[11][1:], (642, 672))
        self.assertEqual(aos[12][1:], (931, 933))
        self.assertEqual(aos[13][1:], (1542, 1547))
        self.assertEqual(aos[14][1:], (1696, 1702))

    def test_002c_video_annotation_objects_in_frame(self):
        video_football = models.repository.videos.get_one_by_id(1)
        self.assertIsNotNone(video_football)

        aos = video_football.annotation_objects_in_frame(200)
        self.assertEqual(len(aos), 2)

        # correctly ordered?
        self.assertEqual(aos[0][1:], (124, 325))
        self.assertEqual(aos[1][1:], (139, 337))


        aos = video_football.annotation_objects_in_frame(200000)
        self.assertEqual(len(aos), 0)

    def test_002d_video_annotation_objects_in_frame_intervals(self):
        video_football = models.repository.videos.get_one_by_id(1)
        self.assertIsNotNone(video_football)

        aos = video_football.annotation_objects_in_frame_intervals([])
        self.assertEqual(len(aos), 0)

        aos = video_football.annotation_objects_in_frame_intervals([(20000,20000)])
        self.assertEqual(len(aos), 0)

        aos = video_football.annotation_objects_in_frame_intervals([(330,20000)])
        self.assertEqual(len(aos), 10)

        aos = video_football.annotation_objects_in_frame_intervals([(200,200)])
        self.assertEqual(len(aos), 2)

        aos = video_football.annotation_objects_in_frame_intervals([(14,320)])
        self.assertEqual(len(aos), 5)

        aos = video_football.annotation_objects_in_frame_intervals([(0,10), (330,500)])
        self.assertEqual(len(aos), 5)

        aos = video_football.annotation_objects_in_frame_intervals([(30,30), (330,330), (20000,20000)])
        self.assertEqual(len(aos), 3)

    def test_002e_video_annotation_objects_in_frame_intervals_filter_object_ids(self):
        video_football = models.repository.videos.get_one_by_id(1)
        self.assertIsNotNone(video_football)

        aos = video_football.annotation_objects_in_frame_intervals([(330,20000)], filter_object_ids=[10, 11, 12])
        self.assertEqual(len(aos), 3)

    def test_002f_video_annotation_objects_in_frame_intervals_joins(self):
        # pre-load all annotation_attributes
        # (so that they are not lazily loaded later during measurement of number of SQL executions)
        aas = models.repository.annotation_attributes.get_all()

        video_football = models.repository.videos.get_one_by_id(1)
        self.assertIsNotNone(video_football)

        aos = video_football.annotation_objects_in_frame_intervals([(330,20000)])
        self.assertEqual(len(aos), 10)
        ao = aos[0][0]

        self.assertEqual(ao.id, 5)

        # no SQL should be executed now, annotation_values should be already eagerly loaded for all annotation objects returned by annotation_objects_in_frame_intervals()
        sql_count_1 = models.database.db.profiler['sql_count']
        avs = ao.annotation_values_local()
        self.assertEqual(len(avs), 7)

        avs = ao.annotation_values_local_interpolate_in_frame(330, interpolation=0)
        self.assertEqual(len(avs), 0)

        avs = ao.annotation_values_local_interpolate_in_frame(337, interpolation=0)
        self.assertEqual(len(avs), 1)

        sql_count_2 = models.database.db.profiler['sql_count']
        self.assertEqual(sql_count_1, sql_count_2)

    def test_002g_video_annotation_objects_import(self):
        annotator_admin = models.repository.annotators.get_one_enabled_by_name(u"admin")

        with open(os.path.join(os.path.dirname(__file__), 'fixtures_2.json')) as fr:
            data = json.load(fr)

        for name, aos_data in data.iteritems():
            # name can be video's name or filename, try to select by both
            video = models.repository.videos.get_one_by_filename(name) or models.repository.videos.get_one_by_name(name)

            annotation_objects_count_before = len(video.annotation_objects_all())

            video.import_annotations(aos_data, annotator=annotator_admin)

            annotation_objects_count_after = len(video.annotation_objects_all())

            self.assertEqual(annotation_objects_count_before + 2, annotation_objects_count_after)

    def test_002h_video_annotation_object_next(self):
        video_football = models.repository.videos.get_one_by_id(1)
        self.assertIsNotNone(video_football)

        ao3 = models.repository.annotation_objects.get_one_by_id(3)
        self.assertIsNotNone(ao3)

        ao4 = models.repository.annotation_objects.get_one_by_id(4)
        self.assertIsNotNone(ao3)

        ao5 = models.repository.annotation_objects.get_one_by_id(5)
        self.assertIsNotNone(ao5)

        # annotation_object_next
        r = video_football.annotation_object_next(10000)
        self.assertIsNone(r)

        ao, frame_from, frame_to = video_football.annotation_object_next(140)
        self.assertEqual(ao.id, 17)
        self.assertEqual(frame_from, 142)
        self.assertEqual(frame_to, 333)

        ao, frame_from, frame_to = video_football.annotation_object_next(140, ao3)
        self.assertEqual(ao.id, 5)
        self.assertEqual(frame_from, 139)
        self.assertEqual(frame_to, 337)

        ao, frame_from, frame_to = video_football.annotation_object_next(140, ao5)
        self.assertEqual(ao.id, 17)
        self.assertEqual(frame_from, 142)
        self.assertEqual(frame_to, 333)

        ao, frame_from, frame_to = video_football.annotation_object_next(0, ao4)
        self.assertEqual(ao.id, 16)

        ao, frame_from, frame_to = video_football.annotation_object_next(0)
        self.assertEqual(ao.id, 2)

        ao, frame_from, frame_to = video_football.annotation_object_next(1)
        self.assertEqual(ao.id, 2)

        # annotation_object_previous
        r = video_football.annotation_object_previous(0)
        self.assertIsNone(r)

        ao, frame_from, frame_to = video_football.annotation_object_previous(140)
        self.assertEqual(ao.id, 2)
        self.assertEqual(frame_from, 31)
        self.assertEqual(frame_to, 123)

        ao, frame_from, frame_to = video_football.annotation_object_previous(140, ao5)
        self.assertEqual(ao.id, 3)
        self.assertEqual(frame_from, 124)
        self.assertEqual(frame_to, 325)

        ao, frame_from, frame_to = video_football.annotation_object_previous(140, ao3)
        self.assertEqual(ao.id, 2)
        self.assertEqual(frame_from, 31)
        self.assertEqual(frame_to, 123)

        ao, frame_from, frame_to = video_football.annotation_object_previous(0, ao4)
        self.assertEqual(ao.id, 1)

        ao, frame_from, frame_to = video_football.annotation_object_previous(31)
        self.assertEqual(ao.id, 16)

        ao, frame_from, frame_to = video_football.annotation_object_previous(32)
        self.assertEqual(ao.id, 16)

    def test_002i_video_options(self):
        annotator_admin = models.repository.annotators.get_one_enabled_by_name(u"admin")
        video_football = video_football = models.repository.videos.get_one_by_id(1)
        self.assertEquals(video_football.get_option(['gui', 'color', 'annotation_object_visual']), '#00ffff')
        self.assertEquals(video_football.get_option('gui.color.annotation_object_visual'), '#00ffff')

        try:
            annotator_admin.get_option(['foo'])
        except:
            pass
        else:
            self.fail()


    def test_003a_annotation_attribute_repr(self):
        annotation_attribute_new = models.entity.AnnotationAttribute(name=u'ěšč')
        self.assertTrue(str(annotation_attribute_new).startswith('<AnnotationAttribute#None('))

    def test_003b_annotation_attribute_options(self):
        aa = models.repository.annotation_attributes.get_one_by_id(1)

        self.assertEquals(aa.get_option(['gui', 'color', 'annotation_object_visual']), 'blue')
        self.assertEquals(aa.get_option('gui.color.annotation_object_visual'), 'blue')

        try:
            aa.get_option(['foo'])
        except:
            pass
        else:
            self.fail()

    def test_004a_annotation_value_repr(self):
        annotation_attribute_new = models.entity.AnnotationAttribute(data_type=u'unicode')
        annotation_value_new = models.entity.AnnotationValue(value=u'ěšč', annotation_attribute=annotation_attribute_new)
        self.assertTrue(str(annotation_value_new).startswith('<AnnotationValue#None('))

    def test_004b_annotation_value_interpolate_float(self):
        v = models.entity.AnnotationValue.interpolate_float((1.0, -1.0), (2.0, 1.0), 1.5)
        self.assertAlmostEqual(v, 0.0)

        v = models.entity.AnnotationValue.interpolate_float((1, -1), (2, 1), 1.5)
        self.assertAlmostEqual(v, 0.0)

        v = models.entity.AnnotationValue.interpolate_float(None, (2, 1), 1.5)
        self.assertAlmostEqual(v, 1.0)

        v = models.entity.AnnotationValue.interpolate_float((2, 1), None, 1.5)
        self.assertAlmostEqual(v, 1.0)

        v = models.entity.AnnotationValue.interpolate_float(None, None, 1.5)
        self.assertIsNone(v)

    def test_004c_annotation_value_options(self):
        av = models.repository.annotation_values.get_one_by_id(1)

        self.assertEquals(av.get_option(['gui', 'color', 'annotation_object_visual']), '#00ffff')
        self.assertEquals(av.get_option('gui.color.annotation_object_visual'), '#00ffff')

        av.options = json.dumps({'gui': {'color': {'annotation_object_visual': 'black'}}})

        self.assertEquals(av.get_option('gui.color.annotation_object_visual'), 'black')

        try:
            av.get_option(['foo'])
        except:
            pass
        else:
            self.fail()

    def test_004d_annotation_value_autocomplete_values(self):
        aa_comment = models.repository.annotation_attributes.get_one_by_id(100)

        v = aa_comment.autocomplete_values()
        self.assertEquals(v, [u'goal celebration', u'goal celebration with jumping', u'shot on goal'])

        v = aa_comment.autocomplete_values('celebration')
        self.assertEquals(v, [u'goal celebration', u'goal celebration with jumping'])

        v = aa_comment.autocomplete_values('xxx')
        self.assertEquals(v, [])

    def test_005a_annotation_object_repr(self):
        annotation_object_new = models.entity.AnnotationObject()
        self.assertTrue(str(annotation_object_new).startswith('<AnnotationObject#None('))

    def test_005b_annotation_object_get_text(self):
        ao_comment_2 = models.repository.annotation_objects.get_one_by_id(7)
        text_global, text_local = ao_comment_2.get_text()
        self.assertEquals(text_global, u"") # no global attributes, so it's empty
        self.assertEquals(text_local, u"") # no frame was given, so it's empty

        text_global, text_local = ao_comment_2.get_text(322)
        self.assertTrue(text_local.find(u"celebration") > -1)
        self.assertTrue(text_local.find(u"jumping") == -1)

        sql_count_1 = models.database.db.profiler['sql_count']

        text_global, text_local = ao_comment_2.get_text(362)
        self.assertTrue(text_local.find(u"celebration") > -1)
        self.assertTrue(text_local.find(u"jumping") > -1)

        # there should be no database calls
        sql_count_2 = models.database.db.profiler['sql_count']
        self.assertEqual(sql_count_1, sql_count_2)

    def test_005c_annotation_object_annotation_values_global(self):
        ao_football_point_1 = models.repository.annotation_objects.get_one_by_id(5)
        self.assertIsNotNone(ao_football_point_1)

        avs = ao_football_point_1.annotation_values_global()
        self.assertEqual(len(avs), 1)
        self.assertEqual(avs[0].value, u"gate left bottom")

    def test_005d_annotation_object_annotation_values_local(self):
        ao_football_point_1 = models.repository.annotation_objects.get_one_by_id(5)
        self.assertIsNotNone(ao_football_point_1)

        avs = ao_football_point_1.annotation_values_local()
        self.assertEqual(len(avs), 7)

    def test_005e_annotation_object_annotation_values_local_grouped(self):
        ao_football_rectangle_2 = models.repository.annotation_objects.get_one_by_id(2)
        self.assertIsNotNone(ao_football_rectangle_2)

        avsg = ao_football_rectangle_2.annotation_values_local_grouped()

        lengths = sorted([len(v) for k,v in avsg.iteritems()])

        # there are 2 different annotation attributes, one with 1 annotation value and one with 4 annotation values
        self.assertEqual(lengths, [1, 4])

    def test_005f_annotation_object_annotation_values_local_interpolate_in_frame_no_interpolation(self):
        ao_football_rectangle_1 = models.repository.annotation_objects.get_one_by_id(1)
        self.assertIsNotNone(ao_football_rectangle_1)

        avsi = ao_football_rectangle_1.annotation_values_local_interpolate_in_frame(0, interpolation=False)
        self.assertEqual(len(avsi), 2)
        avsi = ao_football_rectangle_1.annotation_values_local_interpolate_in_frame(0)
        self.assertEqual(len(avsi), 2)

        avsi = ao_football_rectangle_1.annotation_values_local_interpolate_in_frame(15, interpolation=False)
        self.assertEqual(len(avsi), 1)
        avsi = ao_football_rectangle_1.annotation_values_local_interpolate_in_frame(15)
        self.assertEqual(len(avsi), 2)

        avsi = ao_football_rectangle_1.annotation_values_local_interpolate_in_frame(1, interpolation=False)
        self.assertEqual(len(avsi), 0)
        avsi = ao_football_rectangle_1.annotation_values_local_interpolate_in_frame(1)
        self.assertEqual(len(avsi), 2)

    def test_005g_annotation_object_annotation_values_local_interpolate_in_frame(self):
        ao_football_rectangle_1 = models.repository.annotation_objects.get_one_by_id(1)
        self.assertIsNotNone(ao_football_rectangle_1)

        avsi = ao_football_rectangle_1.annotation_values_local_interpolate_in_frame(8)
        self.assertEqual(len(avsi), 2)
        av_activity, av_rectangle_position = (avsi[0], avsi[1]) if avsi[0].annotation_attribute.data_type==u'unicode' else (avsi[1], avsi[0])

        self.assertEqual(av_activity.value, u'walking')
        self.assertEqual(av_activity.is_interpolated, True)

        self.assertEqual(av_rectangle_position.value, (245, 238, 257, 260))
        self.assertEqual(av_rectangle_position.is_interpolated, True)

    def test_005h_annotation_object_annotation_values_local_interpolate_in_frame_expunge_and_rollback(self):
        ao_football_rectangle_1 = models.repository.annotation_objects.get_one_by_id(1)
        self.assertIsNotNone(ao_football_rectangle_1)
        self.assertEqual(len(ao_football_rectangle_1.annotation_values_local()), 4)

        # create new interpolated annotation value objects in frame 8
        avsi = ao_football_rectangle_1.annotation_values_local_interpolate_in_frame(8)
        self.assertEqual(len(avsi), 2)
        self.assertEqual(len(ao_football_rectangle_1.annotation_values_local()), 4)

        # commit - interpolated annotation values should not be added to database by default,
        # i.e. no change should be made in database
        models.database.db.session.commit()

        avsi = ao_football_rectangle_1.annotation_values_local_interpolate_in_frame(8)
        self.assertEqual(len(avsi), 2)
        self.assertTrue(avsi[0].is_interpolated)
        self.assertTrue(avsi[1].is_interpolated)
        self.assertEqual(len(ao_football_rectangle_1.annotation_values_local()), 4)

        # add interpolated values to database with commit
        avsi[0].database_session_add()
        avsi[1].database_session_add()
        models.database.db.session.commit()

        avsi = ao_football_rectangle_1.annotation_values_local_interpolate_in_frame(8)
        self.assertEqual(len(avsi), 2)
        self.assertFalse(avsi[0].is_interpolated) # not interpolated, values are in database now
        self.assertFalse(avsi[1].is_interpolated)
        self.assertEqual(len(ao_football_rectangle_1.annotation_values_local()), 6) # 2 new objects

        # add other new 2 objects, in frame 9, without commit
        avsi = ao_football_rectangle_1.annotation_values_local_interpolate_in_frame(9)

        self.assertEqual(len(avsi), 2)
        self.assertTrue(avsi[0].is_interpolated)
        self.assertTrue(avsi[1].is_interpolated)
        self.assertEqual(len(ao_football_rectangle_1.annotation_values_local()), 6)

        # add interpolated values to database
        avsi[0].database_session_add()
        avsi[1].database_session_add()
        # no commit here!

        avsi = ao_football_rectangle_1.annotation_values_local_interpolate_in_frame(8)

        self.assertEqual(len(avsi), 2)
        self.assertFalse(avsi[0].is_interpolated) # not interpolated, values are in database transaction now
        self.assertFalse(avsi[1].is_interpolated)
        self.assertEqual(len(ao_football_rectangle_1.annotation_values_local()), 8) # 2 new objects

        # make change in different table, test multitable rollback
        annotator_pavel = models.repository.annotators.get_one_enabled_by_name(u"Pavel Campr")
        annotator_pavel.name = u"Changed name of Pavel"

        # rollback, should remove 2 new objects pending in transaction
        models.database.db.session.flush() # send all pending changes to database, still keep transaction opened
        models.database.db.session.rollback()

        avsi = ao_football_rectangle_1.annotation_values_local_interpolate_in_frame(9)

        self.assertEqual(len(avsi), 2)
        self.assertTrue(avsi[0].is_interpolated)
        self.assertTrue(avsi[1].is_interpolated)
        self.assertEqual(len(ao_football_rectangle_1.annotation_values_local()), 6) # 2 new objects were rollbacked

        # verify that rollback succeeded in different table
        annotator_pavel = models.repository.annotators.get_one_enabled_by_name(u"Pavel Campr")
        self.assertTrue(str(annotator_pavel).startswith('<Annotator#2('))

    def test_005i_annotation_object_active_interval(self):
        ao_football_rectangle_1 = models.repository.annotation_objects.get_one_by_id(1)
        self.assertIsNotNone(ao_football_rectangle_1)

        active_interval = ao_football_rectangle_1.active_interval()

        self.assertEqual(active_interval, (0,30))

    def test_005j_annotation_object_is_active_in_frame(self):
        ao_football_rectangle_1 = models.repository.annotation_objects.get_one_by_id(1)
        self.assertIsNotNone(ao_football_rectangle_1)

        self.assertTrue(ao_football_rectangle_1.is_active_in_frame(0))
        self.assertTrue(ao_football_rectangle_1.is_active_in_frame(15))
        self.assertTrue(ao_football_rectangle_1.is_active_in_frame(30))
        self.assertFalse(ao_football_rectangle_1.is_active_in_frame(50))

    def test_005k_annotation_object_options(self):
        ao = models.repository.annotation_objects.get_one_by_id(1)

        self.assertEquals(ao.get_option(['gui', 'color', 'annotation_object_visual']), '#00ffff')
        self.assertEquals(ao.get_option('gui.color.annotation_object_visual'), '#00ffff')

        try:
            ao.get_option(['foo'])
        except:
            pass
        else:
            self.fail()

    def test_100a_annotation_object_delete_cascade(self):
        values_len_1 = len(models.repository.annotation_values.get_all())

        ao_football_rectangle_1 = models.repository.annotation_objects.get_one_by_id(1)
        self.assertIsNotNone(ao_football_rectangle_1)

        models.database.db.session.delete(ao_football_rectangle_1)
        models.database.db.session.commit()

        values_len_2 = len(models.repository.annotation_values.get_all())

        # some AnnotationValue objects were deleted in cascade
        self.assertGreater(values_len_1, values_len_2)

    def test_100b_video_delete_cascade(self):
        values_len_1 = len(models.repository.annotation_values.get_all())
        objects_len_1 = len(models.repository.annotation_objects.get_all())

        video_football = models.repository.videos.get_one_by_id(1)
        self.assertIsNotNone(video_football)

        models.database.db.session.delete(video_football)
        models.database.db.session.commit()

        values_len_2 = len(models.repository.annotation_values.get_all())
        objects_len_2 = len(models.repository.annotation_objects.get_all())

        # some objects were deleted in cascade
        self.assertGreater(values_len_1, values_len_2)
        self.assertGreater(objects_len_1, objects_len_2)


if __name__ == '__main__':
    unittest.main()
