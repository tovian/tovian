# -*- coding: utf-8 -*-

__version__ = "$Id: defaults.py 318 2013-11-21 09:12:44Z campr $"

import entity


def create_defaults():
    # annotation attributes - positional
    aa_position_rectangle = entity.AnnotationAttribute(id=1, name=u'position_rectangle', data_type=u'position_rectangle',
                                                       annotation_object_type=u'rectangle', is_global=False)
    aa_position_circle = entity.AnnotationAttribute(id=2, name=u'position_circle', data_type=u'position_circle',
                                                    annotation_object_type=u'circle', is_global=False)
    aa_position_point = entity.AnnotationAttribute(id=3, name=u'position_point', data_type=u'position_point',
                                                   annotation_object_type=u'point', is_global=False)
    aa_position_nonvisual = entity.AnnotationAttribute(id=4, name=u'position_nonvisual', data_type=u'position_nonvisual',
                                                   annotation_object_type=u'nonvisual', is_global=False)

    # annotation attributes - universal
    aa_comment = entity.AnnotationAttribute(id=100, name=u'comment', data_type=u'unicode',
                                            annotation_object_type=u'nonvisual', is_global=False)
    aa_shot_change = entity.AnnotationAttribute(id=101, name=u'shot_change', data_type=u'unicode',
                                                annotation_object_type=u'nonvisual', is_global=True,
                                                allowed_values=[u"cut", u"fade", u"dissolve", u"other", u"???"])
    aa_ignored = entity.AnnotationAttribute(id=102, name=u'ignored', data_type=u'unicode',
                                                annotation_object_type=u'nonvisual', is_global=True)
    return (aa_position_rectangle, aa_position_circle, aa_position_point, aa_position_nonvisual, aa_comment, aa_shot_change, aa_ignored)
