# -*- coding: utf-8 -*-

import tovian.models.entity as entity
import tovian.models.defaults as defaults


def create_fixtures():
    """
    Create objects for testing purposes.

    :rtype: list of objects
    """

    fixtures = []

    # annotators
    annotator_admin = entity.Annotator(id=1, name=u"admin", is_enabled=True,
                                       email=u"admin@abc.cz", password=u"admin123")
    annotator_pavel = entity.Annotator(id=2, name=u"Pavel Campr", is_enabled=True, master=annotator_admin,
                                       email=u"campr@kky.zcu.cz", password=u"pavel123")
    annotator_milan = entity.Annotator(id=3, name=u"Milan Herbig", is_enabled=True, master=annotator_pavel,
                                       email=u"herbig@students.zcu.cz", password=u"milan123")
    annotator_foo = entity.Annotator(id=4, name=u"Test Foo", is_enabled=False, master=annotator_pavel,
                                     email=u"foo@abc.cz", password=u"foo123")

    fixtures += [annotator_admin, annotator_pavel, annotator_milan, annotator_foo]


    # videos
    video_football = entity.Video(id=1, name=u"Test Football 1", filename=u"test_football.mp4",
                                  url_download=u"http://konos-pole2-kky.fav.zcu.cz/cemi/tovian/test_football.mp4",
                                  frame_count=1799, fps=29.97, width=512, height=288, duration=60.03,
                                  is_enabled=True, is_finished=False,
                                  allowed_annotation_object_types=u'rectangle circle point nonvisual',
                                  uploader=annotator_pavel,
                                  annotators=[annotator_pavel, annotator_milan, annotator_foo, annotator_admin],
                                  public_comment=u"Testing annotation - football match", options='{"gui": {"color": {"annotation_object_visual": "#00ffff"}}}')

    video_parliament_1 = entity.Video(id=2, name=u"Test Parliament 1", filename=u"test_parlament.mp4",
                                      url_download=u"http://konos-pole2-kky.fav.zcu.cz/cemi/tovian/test_parlament.mp4",
                                      frame_count=6000, fps=25, width=1024, height=576, duration=240.0,
                                      is_enabled=True, is_finished=False,
                                      allowed_annotation_object_types=u'rectangle',
                                      uploader=annotator_pavel,
                                      annotators=[annotator_pavel, annotator_milan, annotator_foo],
                                      public_comment=u"Testing annotation - parliament meeting 1 (faces)")

    video_parliament_2 = entity.Video(id=3, name=u"Test Parliament 2", filename=u"test_parlament.mp4",
                                      url_download=u"http://konos-pole2-kky.fav.zcu.cz/cemi/tovian/test_parlament.mp4",
                                      frame_count=6000, fps=25, width=1024, height=576, duration=240.0,
                                      is_enabled=True, is_finished=False,
                                      allowed_annotation_object_types=u'rectangle point',
                                      uploader=annotator_pavel,
                                      annotators=[annotator_pavel, annotator_milan, annotator_foo],
                                      public_comment=u"Testing annotation - parliament meeting 2 (faces and landmarks)")

    video_parliament_3 = entity.Video(id=4, name=u"Test Parliament 3", filename=u"test_parlament.mp4",
                                      url_download=u"http://konos-pole2-kky.fav.zcu.cz/cemi/tovian/test_parlament.mp4",
                                      frame_count=6000, fps=25, width=1024, height=576, duration=240.0,
                                      is_enabled=True, is_finished=True,
                                      allowed_annotation_object_types=u'rectangle circle point',
                                      uploader=annotator_pavel,
                                      annotators=[annotator_pavel, annotator_milan, annotator_foo],
                                      public_comment=u"Testing annotation - parliament meeting 3 (finished)")

    video_parliament_4 = entity.Video(id=5, name=u"Test Parliament 4", filename=u"test_parlament.mp4",
                                      url_download=u"http://konos-pole2-kky.fav.zcu.cz/cemi/tovian/test_parlament.mp4",
                                      frame_count=6000, fps=25, width=1024, height=576, duration=240.0,
                                      is_enabled=False, is_finished=False,
                                      allowed_annotation_object_types=u'rectangle circle point',
                                      uploader=annotator_pavel,
                                      annotators=[annotator_pavel, annotator_milan, annotator_foo],
                                      public_comment=u"Testing annotation - parliament meeting 4 (disabled)")

    video_parliament_5 = entity.Video(id=6, name=u"Test Parliament 5", filename=u"test_parlament.mp4",
                                      url_download=u"http://konos-pole2-kky.fav.zcu.cz/cemi/tovian/test_parlament.mp4",
                                      frame_count=6000, fps=25, width=1024, height=576, duration=240.0,
                                      is_enabled=False, is_finished=True,
                                      allowed_annotation_object_types=u'rectangle circle point',
                                      uploader=annotator_pavel, annotators=[annotator_admin],
                                      public_comment=u"Testing annotation - parliament meeting 5 (disabled)")

    video_traffic_1 = entity.Video(id=7, name=u"Test Traffic 1", filename=u"test_traffic_1.mts",
                                  url_download=u"http://konos-pole2-kky.fav.zcu.cz/cemi/tovian/test_traffic_1.mts",
                                  frame_count=654, fps=23.98, width=1920, height=1080, duration=27.26,
                                  is_enabled=True, is_finished=False,
                                  allowed_annotation_object_types=u'rectangle circle point',
                                  uploader=annotator_pavel,
                                  annotators=[annotator_pavel, annotator_milan, annotator_foo],
                                  public_comment=u"Testing annotation - traffic [HD]", )

    video_parliament_6 = entity.Video(name=u"Test Parliament 16:10", filename=u"test_parlament_912x570.mp4",
                                      url_download=u"http://konos-pole2-kky.fav.zcu.cz/cemi/tovian/test_parlament_912x570.mp4",
                                      frame_count=802, fps=25, width=912, height=570, duration=32.1,
                                      is_enabled=True, is_finished=False,
                                      allowed_annotation_object_types=u'rectangle',
                                      uploader=annotator_pavel, annotators=[annotator_admin, annotator_milan],
                                      public_comment=u"Testing annotation - parliament meeting - 16:10")

    video_parliament_7 = entity.Video(name=u"Test Parliament 16:10", filename=u"test_parlament_768x576.mp4",
                                      url_download=u"http://konos-pole2-kky.fav.zcu.cz/cemi/tovian/test_parlament_768x576.mp4",
                                      frame_count=802, fps=25, width=768, height=576, duration=32.1,
                                      is_enabled=True, is_finished=False,
                                      allowed_annotation_object_types=u'rectangle',
                                      uploader=annotator_pavel, annotators=[annotator_admin, annotator_milan],
                                      public_comment=u"Testing annotation - parliament meeting - 4:3")

    video_parliament_8 = entity.Video(name=u"Test Parliament vertical", filename=u"test_parlament_280x570.mp4",
                                      url_download=u"http://konos-pole2-kky.fav.zcu.cz/cemi/tovian/test_parlament_280x570.mp4",
                                      frame_count=802, fps=25, width=280, height=570, duration=32.1,
                                      is_enabled=True, is_finished=False,
                                      allowed_annotation_object_types=u'rectangle',
                                      uploader=annotator_pavel, annotators=[annotator_admin, annotator_milan],
                                      public_comment=u"Testing annotation - parliament meeting - vertical")

    video_kratke = entity.Video(name=u"Velmi kratke video", filename=u"signs_green_new_records.avi",
                                      url_download=u"http://konos-pole2-kky.fav.zcu.cz/tovian/dopanar/signs_green_new_records.avi",
                                      frame_count=123, fps=25, width=1920, height=1080, duration=4.92,
                                      is_enabled=True, is_finished=False,
                                      allowed_annotation_object_types=u'rectangle',
                                      uploader=annotator_pavel, annotators=[annotator_admin, annotator_milan],
                                      public_comment=u"Testing annotation on very short video")

    fixtures += [video_football, video_parliament_1, video_parliament_2, video_parliament_3,
                 video_parliament_4, video_parliament_5, video_traffic_1, video_parliament_6, video_parliament_7,
                 video_parliament_8, video_kratke]


    # annotation attributes - universal
    aa_position_rectangle, aa_position_circle, aa_position_point, aa_position_nonvisual, aa_comment, aa_shot_change, aa_ignored = defaults.create_defaults()

    fixtures += [aa_position_rectangle, aa_position_circle, aa_position_point, aa_position_nonvisual, aa_comment, aa_shot_change, aa_ignored]


    # annotation attributes - custom
    aa_parliament_identity_1 = entity.AnnotationAttribute(id=1000, name=u'parliament_identity_1', data_type=u'unicode',
                                                          annotation_object_type=u'rectangle', is_global=True,
                                                          allowed_values=[u"Němcová Miroslava", u"Nečas Petr",
                                                                          u"Sivera František", u"Peake Karolína"])
    aa_parliament_overlap_1 = entity.AnnotationAttribute(id=1001, name=u'parliament_overlap_1', data_type=u'unicode',
                                                         annotation_object_type=u'rectangle', is_global=False,
                                                         allowed_values=[u"no overlap", u"small overlap",
                                                                         u"large overlap", u"huge overlap"])
    aa_parliament_is_speaking_1 = entity.AnnotationAttribute(id=1002, name=u'parliament_activity_is_speaking_1',
                                                             data_type=u'bool',
                                                             annotation_object_type=u'rectangle', is_global=False)
    aa_parliament_landmark_1 = entity.AnnotationAttribute(id=1003, name=u'parliament_landmark_1', data_type=u'unicode',
                                                          annotation_object_type=u'point', is_global=True,
                                                          allowed_values=[u"eye left", u"eye right", u"nose"])

    fixtures += [aa_parliament_identity_1, aa_parliament_overlap_1, aa_parliament_is_speaking_1,
                 aa_parliament_landmark_1]

    aa_football_identity_1 = entity.AnnotationAttribute(id=1004, name=u'football_identity_1', data_type=u'unicode',
                                                        annotation_object_type=u'rectangle', is_global=True,
                                                        allowed_values=[u"white player", u"yellow player",
                                                                        u"blue player"])
    aa_football_activity_1 = entity.AnnotationAttribute(id=1005, name=u'football_activity_1', data_type=u'unicode',
                                                        annotation_object_type=u'rectangle', is_global=False,
                                                        allowed_values=[u"", u"walking", u"running",
                                                                        u"running with ball", u"shooting"])
    aa_football_object_1 = entity.AnnotationAttribute(id=1006, name=u'football_object_1', data_type=u'unicode',
                                                      annotation_object_type=u'circle',
                                                      is_global=True, allowed_values=[u"-", u"ball"])
    aa_football_object_2 = entity.AnnotationAttribute(id=1007, name=u'football_object_2', data_type=u'unicode',
                                                      annotation_object_type=u'point', is_global=True,
                                                      allowed_values=[u"-", u"gate left bottom", u"gate right bottom",
                                                                      u"gate left top", u"gate right top"])

    fixtures += [aa_football_identity_1, aa_football_activity_1, aa_football_object_1, aa_football_object_2]


    # video + annotation attributes relations
    video_parliament_1.annotation_attributes = [aa_position_rectangle, aa_parliament_identity_1,
                                                aa_parliament_overlap_1, aa_parliament_is_speaking_1]
    video_parliament_2.annotation_attributes = [aa_position_rectangle, aa_position_point, aa_parliament_identity_1,
                                                aa_parliament_is_speaking_1, aa_parliament_landmark_1]
    video_parliament_3.annotation_attributes = [aa_position_rectangle, aa_parliament_identity_1,
                                                aa_parliament_is_speaking_1]
    video_parliament_4.annotation_attributes = [aa_position_rectangle, aa_parliament_identity_1,
                                                aa_parliament_is_speaking_1]
    video_parliament_5.annotation_attributes = [aa_position_rectangle, aa_parliament_identity_1,
                                                aa_parliament_overlap_1, aa_parliament_is_speaking_1]
    video_football.annotation_attributes = [aa_position_rectangle, aa_position_circle, aa_position_point,
                                            aa_football_identity_1, aa_football_activity_1, aa_football_object_1,
                                            aa_football_object_2, aa_comment, aa_shot_change]
    video_traffic_1.annotation_attributes = [aa_position_rectangle, aa_position_circle, aa_position_point]


    # annotation values - video_test_football
    #   annotate players (rectangle), ball (circle), gate position (points)

    ao_football_rectangle_1 = entity.AnnotationObject(id=1, type=u'rectangle', video=video_football,
                                                      public_comment=u"Random white player",
                                                      created_by=annotator_pavel, modified_by=annotator_pavel)
    av_football_rectangle_1_position_1 = entity.AnnotationValue(frame_from=0, value=[240, 237, 253, 260],
                                                                annotation_attribute=aa_position_rectangle,
                                                                annotation_object=ao_football_rectangle_1,
                                                                created_by=annotator_pavel, modified_by=annotator_pavel)
    av_football_rectangle_1_position_2 = entity.AnnotationValue(frame_from=15, value=[251, 240, 262, 260],
                                                                annotation_attribute=aa_position_rectangle,
                                                                annotation_object=ao_football_rectangle_1,
                                                                created_by=annotator_pavel, modified_by=annotator_pavel)
    av_football_rectangle_1_position_3 = entity.AnnotationValue(frame_from=30, value=[261, 238, 270, 259],
                                                                annotation_attribute=aa_position_rectangle,
                                                                annotation_object=ao_football_rectangle_1,
                                                                created_by=annotator_pavel, modified_by=annotator_pavel)
    av_football_rectangle_1_identity_1 = entity.AnnotationValue(value=u"white player",
                                                                annotation_attribute=aa_football_identity_1,
                                                                annotation_object=ao_football_rectangle_1,
                                                                created_by=annotator_pavel, modified_by=annotator_pavel)
    av_football_rectangle_1_activity_1 = entity.AnnotationValue(frame_from=0, value=u"walking",
                                                                annotation_attribute=aa_football_activity_1,
                                                                annotation_object=ao_football_rectangle_1,
                                                                created_by=annotator_pavel, modified_by=annotator_pavel)
    fixtures += [ao_football_rectangle_1, av_football_rectangle_1_position_1, av_football_rectangle_1_position_2,
                 av_football_rectangle_1_position_3, av_football_rectangle_1_identity_1,
                 av_football_rectangle_1_activity_1]

    ao_football_rectangle_2 = entity.AnnotationObject(id=2, type=u'rectangle', video=video_football,
                                                      public_comment=u"Random yellow player",
                                                      created_by=annotator_pavel, modified_by=annotator_pavel)
    av_football_rectangle_2_position_1 = entity.AnnotationValue(frame_from=31, value=[202, 41, 323, 288],
                                                                annotation_attribute=aa_position_rectangle,
                                                                annotation_object=ao_football_rectangle_2,
                                                                created_by=annotator_pavel, modified_by=annotator_pavel)
    av_football_rectangle_2_position_2 = entity.AnnotationValue(frame_from=65, value=[147, 45, 276, 260],
                                                                annotation_attribute=aa_position_rectangle,
                                                                annotation_object=ao_football_rectangle_2,
                                                                created_by=annotator_pavel, modified_by=annotator_pavel)
    av_football_rectangle_2_position_3 = entity.AnnotationValue(frame_from=106, value=[281, 119, 365, 259],
                                                                annotation_attribute=aa_position_rectangle,
                                                                annotation_object=ao_football_rectangle_2,
                                                                created_by=annotator_pavel, modified_by=annotator_pavel)
    av_football_rectangle_2_position_4 = entity.AnnotationValue(frame_from=123, value=[182, 138, 305, 259],
                                                                annotation_attribute=aa_position_rectangle,
                                                                annotation_object=ao_football_rectangle_2,
                                                                created_by=annotator_pavel, modified_by=annotator_pavel)
    av_football_rectangle_2_identity_1 = entity.AnnotationValue(value=u"yellow player",
                                                                annotation_attribute=aa_football_identity_1,
                                                                annotation_object=ao_football_rectangle_2,
                                                                created_by=annotator_pavel, modified_by=annotator_pavel)
    av_football_rectangle_2_activity_1 = entity.AnnotationValue(frame_from=31, value=u"",
                                                                annotation_attribute=aa_football_activity_1,
                                                                annotation_object=ao_football_rectangle_2,
                                                                created_by=annotator_pavel, modified_by=annotator_pavel)
    fixtures += [ao_football_rectangle_2, av_football_rectangle_2_position_1, av_football_rectangle_2_position_2,
                 av_football_rectangle_2_position_3, av_football_rectangle_2_position_4,
                 av_football_rectangle_2_identity_1, av_football_rectangle_2_activity_1]

    ao_football_circle_2 = entity.AnnotationObject(id=3, type=u'circle', video=video_football,
                                                   public_comment=u"Moving ball",
                                                   created_by=annotator_pavel, modified_by=annotator_pavel)
    av_football_circle_2_object_1 = entity.AnnotationValue(value=u"ball",
                                                           annotation_attribute=aa_football_object_1,
                                                           annotation_object=ao_football_circle_2,
                                                           created_by=annotator_pavel, modified_by=annotator_pavel)
    av_football_circle_2_position_1 = entity.AnnotationValue(frame_from=124, value=[80, 212, 3.5],
                                                             annotation_attribute=aa_position_circle,
                                                             annotation_object=ao_football_circle_2,
                                                             created_by=annotator_pavel, modified_by=annotator_pavel)
    av_football_circle_2_position_2 = entity.AnnotationValue(frame_from=150, value=[207, 98, 2],
                                                             annotation_attribute=aa_position_circle,
                                                             annotation_object=ao_football_circle_2,
                                                             created_by=annotator_pavel, modified_by=annotator_pavel)
    av_football_circle_2_position_3 = entity.AnnotationValue(frame_from=177, value=[237, 66, 2.5],
                                                             annotation_attribute=aa_position_circle,
                                                             annotation_object=ao_football_circle_2,
                                                             created_by=annotator_pavel, modified_by=annotator_pavel)
    av_football_circle_2_position_4 = entity.AnnotationValue(frame_from=212, value=[270, 119, 2],
                                                             annotation_attribute=aa_position_circle,
                                                             annotation_object=ao_football_circle_2,
                                                             created_by=annotator_pavel, modified_by=annotator_pavel)
    av_football_circle_2_position_5 = entity.AnnotationValue(frame_from=244, value=[324, 178, 2.5],
                                                             annotation_attribute=aa_position_circle,
                                                             annotation_object=ao_football_circle_2,
                                                             created_by=annotator_pavel, modified_by=annotator_pavel)
    av_football_circle_2_position_6 = entity.AnnotationValue(frame_from=280, value=[360, 112, 2.5],
                                                             annotation_attribute=aa_position_circle,
                                                             annotation_object=ao_football_circle_2,
                                                             created_by=annotator_pavel, modified_by=annotator_pavel)
    av_football_circle_2_position_7 = entity.AnnotationValue(frame_from=314, value=[453, 101, 3],
                                                             annotation_attribute=aa_position_circle,
                                                             annotation_object=ao_football_circle_2,
                                                             created_by=annotator_pavel, modified_by=annotator_pavel)
    av_football_circle_2_position_8 = entity.AnnotationValue(frame_from=325, value=[513, 98, 3],
                                                             annotation_attribute=aa_position_circle,
                                                             annotation_object=ao_football_circle_2,
                                                             created_by=annotator_pavel, modified_by=annotator_pavel)
    fixtures += [ao_football_circle_2, av_football_circle_2_object_1, av_football_circle_2_position_1,
                 av_football_circle_2_position_2, av_football_circle_2_position_3, av_football_circle_2_position_4,
                 av_football_circle_2_position_5, av_football_circle_2_position_6, av_football_circle_2_position_7,
                 av_football_circle_2_position_8]

    # circle_1 comes after circle_2
    ao_football_circle_1 = entity.AnnotationObject(id=4, type=u'circle', video=video_football,
                                                   public_comment=u"Not moving ball",
                                                   created_by=annotator_pavel, modified_by=annotator_pavel)
    av_football_circle_1_position_1 = entity.AnnotationValue(frame_from=0, value=[37, 202, 1.5],
                                                             annotation_attribute=aa_position_circle,
                                                             annotation_object=ao_football_circle_1,
                                                             created_by=annotator_pavel, modified_by=annotator_pavel)
    av_football_circle_1_position_2 = entity.AnnotationValue(frame_from=12, value=[35, 202, 1.5],
                                                             annotation_attribute=aa_position_circle,
                                                             annotation_object=ao_football_circle_1,
                                                             created_by=annotator_pavel, modified_by=annotator_pavel)
    av_football_circle_1_object_1 = entity.AnnotationValue(value=u"ball",
                                                           annotation_attribute=aa_football_object_1,
                                                           annotation_object=ao_football_circle_1,
                                                           created_by=annotator_pavel, modified_by=annotator_pavel)
    fixtures += [ao_football_circle_1, av_football_circle_1_position_1, av_football_circle_1_position_2,
                 av_football_circle_1_object_1]

    ao_football_point_1 = entity.AnnotationObject(id=5, type=u'point', video=video_football,
                                                  created_by=annotator_pavel, modified_by=annotator_pavel)
    av_football_point_1_object_2 = entity.AnnotationValue(value=u"gate left bottom",
                                                          annotation_attribute=aa_football_object_2,
                                                          annotation_object=ao_football_point_1,
                                                          created_by=annotator_pavel, modified_by=annotator_pavel)
    av_football_point_1_position_1 = entity.AnnotationValue(frame_from=139, value=[510, 81],
                                                            annotation_attribute=aa_position_point,
                                                            annotation_object=ao_football_point_1,
                                                            created_by=annotator_pavel, modified_by=annotator_pavel)
    av_football_point_1_position_2 = entity.AnnotationValue(frame_from=156, value=[471, 92],
                                                            annotation_attribute=aa_position_point,
                                                            annotation_object=ao_football_point_1,
                                                            created_by=annotator_pavel, modified_by=annotator_pavel)
    av_football_point_1_position_3 = entity.AnnotationValue(frame_from=215, value=[457, 113],
                                                            annotation_attribute=aa_position_point,
                                                            annotation_object=ao_football_point_1,
                                                            created_by=annotator_pavel, modified_by=annotator_pavel)
    av_football_point_1_position_4 = entity.AnnotationValue(frame_from=265, value=[356, 107],
                                                            annotation_attribute=aa_position_point,
                                                            annotation_object=ao_football_point_1,
                                                            created_by=annotator_pavel, modified_by=annotator_pavel)
    av_football_point_1_position_5 = entity.AnnotationValue(frame_from=294, value=[375, 114],
                                                            annotation_attribute=aa_position_point,
                                                            annotation_object=ao_football_point_1,
                                                            created_by=annotator_pavel, modified_by=annotator_pavel)
    av_football_point_1_position_6 = entity.AnnotationValue(frame_from=307, value=[333, 116],
                                                            annotation_attribute=aa_position_point,
                                                            annotation_object=ao_football_point_1,
                                                            created_by=annotator_pavel, modified_by=annotator_pavel)
    av_football_point_1_position_7 = entity.AnnotationValue(frame_from=337, value=[508, 60],
                                                            annotation_attribute=aa_position_point,
                                                            annotation_object=ao_football_point_1,
                                                            created_by=annotator_pavel, modified_by=annotator_pavel)
    # av_football_point_1_position_* are in random order
    fixtures += [ao_football_point_1, av_football_point_1_object_2, av_football_point_1_position_2,
                 av_football_point_1_position_1, av_football_point_1_position_7, av_football_point_1_position_3,
                 av_football_point_1_position_6, av_football_point_1_position_5, av_football_point_1_position_4]

    ao_comment_1 = entity.AnnotationObject(id=6, type=u'nonvisual', video=video_football,
                                         created_by=annotator_pavel, modified_by=annotator_pavel)
    av_comment_1_position_1 = entity.AnnotationValue(frame_from=246, value=None, annotation_attribute=aa_position_nonvisual,
                                          annotation_object=ao_comment_1, created_by=annotator_pavel,
                                          modified_by=annotator_pavel)
    av_comment_1_position_2 = entity.AnnotationValue(frame_from=292, value=None, annotation_attribute=aa_position_nonvisual,
                                          annotation_object=ao_comment_1, created_by=annotator_pavel,
                                          modified_by=annotator_pavel)
    av_comment_1_comment_1 = entity.AnnotationValue(frame_from=246, value=u"shot on goal", annotation_attribute=aa_comment,
                                          annotation_object=ao_comment_1, created_by=annotator_pavel,
                                          modified_by=annotator_pavel)
    fixtures += [ao_comment_1, av_comment_1_position_1, av_comment_1_position_2, av_comment_1_comment_1]

    ao_comment_2 = entity.AnnotationObject(id=7, type=u'nonvisual', video=video_football,
                                         created_by=annotator_pavel, modified_by=annotator_pavel)
    av_comment_2_position_1 = entity.AnnotationValue(frame_from=322, value=None, annotation_attribute=aa_position_nonvisual,
                                          annotation_object=ao_comment_2, created_by=annotator_pavel,
                                          modified_by=annotator_pavel)
    av_comment_2_position_2 = entity.AnnotationValue(frame_from=632, value=None, annotation_attribute=aa_position_nonvisual,
                                          annotation_object=ao_comment_2, created_by=annotator_pavel,
                                          modified_by=annotator_pavel)
    av_comment_2_comment_1 = entity.AnnotationValue(frame_from=322, value=u"goal celebration", annotation_attribute=aa_comment,
                                          annotation_object=ao_comment_2, created_by=annotator_pavel,
                                          modified_by=annotator_pavel)
    av_comment_2_comment_2 = entity.AnnotationValue(frame_from=362, value=u"goal celebration with jumping", annotation_attribute=aa_comment,
                                          annotation_object=ao_comment_2, created_by=annotator_pavel,
                                          modified_by=annotator_pavel)
    fixtures += [ao_comment_2, av_comment_2_position_1, av_comment_2_position_2, av_comment_2_comment_1, av_comment_2_comment_2]

    ao_frame_selection = entity.AnnotationObject(id=8, type=u'nonvisual', video=video_football,
                                         created_by=annotator_pavel, modified_by=annotator_pavel)
    av_frame_selection_1 = entity.AnnotationValue(frame_from=382, value=True, annotation_attribute=aa_position_nonvisual,
                                          annotation_object=ao_frame_selection, created_by=annotator_pavel,
                                          modified_by=annotator_pavel)
    av_frame_selection_2 = entity.AnnotationValue(frame_from=549, value=True, annotation_attribute=aa_position_nonvisual,
                                          annotation_object=ao_frame_selection, created_by=annotator_pavel,
                                          modified_by=annotator_pavel)
    fixtures += [ao_frame_selection, av_frame_selection_1, av_frame_selection_2]

    ao_shot_change_1 = entity.AnnotationObject(id=9, type=u'nonvisual', video=video_football,
                                         created_by=annotator_pavel, modified_by=annotator_pavel)
    av_shot_change_1_type = entity.AnnotationValue(value=u"cut", annotation_attribute=aa_shot_change,
                                          annotation_object=ao_shot_change_1, created_by=annotator_pavel,
                                          modified_by=annotator_pavel)
    av_shot_change_1a = entity.AnnotationValue(frame_from=550, value=True, annotation_attribute=aa_position_nonvisual,
                                          annotation_object=ao_shot_change_1, created_by=annotator_pavel,
                                          modified_by=annotator_pavel)
    fixtures += [ao_shot_change_1, av_shot_change_1_type, av_shot_change_1a]

    ao_shot_change_2 = entity.AnnotationObject(id=10, type=u'nonvisual', video=video_football,
                                         created_by=annotator_pavel, modified_by=annotator_pavel)
    av_shot_change_2_type = entity.AnnotationValue(value=u"cut", annotation_attribute=aa_shot_change,
                                          annotation_object=ao_shot_change_2, created_by=annotator_pavel,
                                          modified_by=annotator_pavel)
    av_shot_change_2a = entity.AnnotationValue(frame_from=627, value=True, annotation_attribute=aa_position_nonvisual,
                                          annotation_object=ao_shot_change_2, created_by=annotator_pavel,
                                          modified_by=annotator_pavel)
    fixtures += [ao_shot_change_2, av_shot_change_2_type, av_shot_change_2a]

    ao_shot_change_3 = entity.AnnotationObject(id=11, type=u'nonvisual', video=video_football,
                                         created_by=annotator_pavel, modified_by=annotator_pavel)
    av_shot_change_3_type = entity.AnnotationValue(value=u"dissolve", annotation_attribute=aa_shot_change,
                                          annotation_object=ao_shot_change_3, created_by=annotator_pavel,
                                          modified_by=annotator_pavel)
    av_shot_change_3a = entity.AnnotationValue(frame_from=633, value=True, annotation_attribute=aa_position_nonvisual,
                                          annotation_object=ao_shot_change_3, created_by=annotator_pavel,
                                          modified_by=annotator_pavel)
    av_shot_change_3b = entity.AnnotationValue(frame_from=635, value=True, annotation_attribute=aa_position_nonvisual,
                                          annotation_object=ao_shot_change_3, created_by=annotator_pavel,
                                          modified_by=annotator_pavel)
    fixtures += [ao_shot_change_3, av_shot_change_3_type, av_shot_change_3a, av_shot_change_3b]

    ao_shot_change_4 = entity.AnnotationObject(id=12, type=u'nonvisual', video=video_football,
                                         created_by=annotator_pavel, modified_by=annotator_pavel)
    av_shot_change_4_type = entity.AnnotationValue(value=u"other", annotation_attribute=aa_shot_change,
                                          annotation_object=ao_shot_change_4, created_by=annotator_pavel,
                                          modified_by=annotator_pavel)
    av_shot_change_4a = entity.AnnotationValue(frame_from=642, value=True, annotation_attribute=aa_position_nonvisual,
                                          annotation_object=ao_shot_change_4, created_by=annotator_pavel,
                                          modified_by=annotator_pavel)
    av_shot_change_4b = entity.AnnotationValue(frame_from=672, value=True, annotation_attribute=aa_position_nonvisual,
                                          annotation_object=ao_shot_change_4, created_by=annotator_pavel,
                                          modified_by=annotator_pavel)
    fixtures += [ao_shot_change_4, av_shot_change_4_type, av_shot_change_4a, av_shot_change_4b]

    ao_shot_change_5 = entity.AnnotationObject(id=13, type=u'nonvisual', video=video_football,
                                         created_by=annotator_pavel, modified_by=annotator_pavel)
    av_shot_change_5_type = entity.AnnotationValue(value=u"dissolve", annotation_attribute=aa_shot_change,
                                          annotation_object=ao_shot_change_5, created_by=annotator_pavel,
                                          modified_by=annotator_pavel)
    av_shot_change_5a = entity.AnnotationValue(frame_from=931, value=True, annotation_attribute=aa_position_nonvisual,
                                          annotation_object=ao_shot_change_5, created_by=annotator_pavel,
                                          modified_by=annotator_pavel)
    av_shot_change_5b = entity.AnnotationValue(frame_from=933, value=True, annotation_attribute=aa_position_nonvisual,
                                          annotation_object=ao_shot_change_5, created_by=annotator_pavel,
                                          modified_by=annotator_pavel)
    fixtures += [ao_shot_change_5, av_shot_change_5_type, av_shot_change_5a, av_shot_change_5b]

    ao_shot_change_6 = entity.AnnotationObject(id=14, type=u'nonvisual', video=video_football,
                                         created_by=annotator_pavel, modified_by=annotator_pavel)
    av_shot_change_6_type = entity.AnnotationValue(value=u"other", annotation_attribute=aa_shot_change,
                                          annotation_object=ao_shot_change_6, created_by=annotator_pavel,
                                          modified_by=annotator_pavel)
    av_shot_change_6a = entity.AnnotationValue(frame_from=1542, value=True, annotation_attribute=aa_position_nonvisual,
                                          annotation_object=ao_shot_change_6, created_by=annotator_pavel,
                                          modified_by=annotator_pavel)
    av_shot_change_6b = entity.AnnotationValue(frame_from=1547, value=True, annotation_attribute=aa_position_nonvisual,
                                          annotation_object=ao_shot_change_6, created_by=annotator_pavel,
                                          modified_by=annotator_pavel)
    fixtures += [ao_shot_change_6, av_shot_change_6_type, av_shot_change_6a, av_shot_change_6b]

    ao_shot_change_7 = entity.AnnotationObject(id=15, type=u'nonvisual', video=video_football,
                                         created_by=annotator_pavel, modified_by=annotator_pavel)
    av_shot_change_7_type = entity.AnnotationValue(value=u"dissolve", annotation_attribute=aa_shot_change,
                                          annotation_object=ao_shot_change_7, created_by=annotator_pavel,
                                          modified_by=annotator_pavel)
    av_shot_change_7a = entity.AnnotationValue(frame_from=1696, value=True, annotation_attribute=aa_position_nonvisual,
                                          annotation_object=ao_shot_change_7, created_by=annotator_pavel,
                                          modified_by=annotator_pavel)
    av_shot_change_7b = entity.AnnotationValue(frame_from=1702, value=True, annotation_attribute=aa_position_nonvisual,
                                          annotation_object=ao_shot_change_7, created_by=annotator_pavel,
                                          modified_by=annotator_pavel)
    fixtures += [ao_shot_change_7, av_shot_change_7_type, av_shot_change_7a, av_shot_change_7b]

    return fixtures
