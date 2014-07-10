# -*- coding: utf-8 -*-

"""
    Entity classes
"""

__version__ = "$Id: entity.py 355 2014-04-15 11:44:14Z campr $"

import logging
from collections import defaultdict

import sqlalchemy
from sqlalchemy import ForeignKey
from sqlalchemy import Table
from sqlalchemy import Column, Integer, Boolean, Float, TIMESTAMP, Unicode, UnicodeText
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref, synonym, subqueryload
from sqlalchemy.sql import func
from sqlalchemy.sql.expression import desc

import security
import database
import repository
import json
import time

from .. import util


logger = logging.getLogger(__name__)
logger.debug('Import ' + __name__)

Base = declarative_base()

default_options = {
    'gui': {
        'color': {
            'annotation_object_visual': 'blue',
            'annotation_object_visual_focus': 'lime',
            'annotation_object_visual_edit': 'red',
            'annotation_object_nonvisual': 'blue',
            'annotation_object_nonvisual_not_interpolated': 'darkBlue',
            'annotation_object_nonvisual_focus': 'lime',
            'annotation_object_nonvisual_focus_not_interpolated': 'darkGreen',
            'annotation_object_nonvisual_edit': 'red'
        }
    }
}

class Annotator(Base):
    """
    Annotators.
    """

    __tablename__ = 'annotators'

    id = Column(Integer, primary_key=True)

    email = Column(Unicode(255), nullable=False, index=True) # used as login name too
    password_hash = Column(Unicode(255), nullable=False)
    name = Column(Unicode(255), nullable=False, index=True)
    phone = Column(Unicode(255))
    internal_comment = Column(UnicodeText)
    is_enabled = Column(Boolean, index=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    modified_at = Column(TIMESTAMP, onupdate=func.current_timestamp())
    options = Column(UnicodeText)

    master_id = Column(Integer, ForeignKey('annotators.id'))
    slaves = relationship('Annotator', backref=backref('master', remote_side=[id]))

    logger.debug('Initialized Annotator')

    @property
    def password(self):
        raise Exception("Cannot get password")

    @password.setter
    def password(self, value):
        if len(value) < 6:
            raise Exception("Password must be at least 6 characters long")

        self.password_hash = unicode(security.hash_password(value))

    def __repr__(self):
        return "<Annotator#%s(%s,%s)>" % (str(self.id), unicode(self.name).encode('utf8'), 'enabled' if self.is_enabled else 'disabled')

    def match_password(self, password):
        return security.match_password(password, self.password_hash)

    def videos_to_annotate(self):
        """
        Returns videos that can be annotated by this user

        :rtype: list of Video
        """

        q = database.db.session.query(Video)
        q = q.filter_by(is_enabled=True)
        q = q.filter(Video.annotators.any(id=self.id))

        return q.all()

    def video_to_annotate_by_id(self, id):
        """
        Returns video by id that can be annotated by this user

        :rtype: Video or None
        """
        try:
            q = database.db.session.query(Video)
            q = q.filter_by(is_enabled=True, is_finished=False, id=id)
            q = q.filter(Video.annotators.any(id=self.id))

            return q.one()

        except sqlalchemy.orm.exc.NoResultFound, sqlalchemy.orm.exc.MultipleResultsFound:
            return None

    def get_option(self, key=[], use_defaults=True):
        try:
            entity_options = json.loads(self.options)
        except:
            entity_options = {}

        if use_defaults:
            options = util.dict_merge(default_options, entity_options)
        else:
            options = entity_options

        if isinstance(key, basestring):
            key = key.split('.')

        for k in key:
            options = options[k]

        return options


table_bind_video_to_annotator = Table('bind_video_to_annotator', Base.metadata,
                                      Column('video_id', Integer, ForeignKey('videos.id', ondelete='CASCADE')),
                                      Column('annotator_id', Integer, ForeignKey('annotators.id'))
)


class Video(Base):
    """
    Videos to annotate.
    """

    __tablename__ = 'videos'

    id = Column(Integer, primary_key=True)

    name = Column(UnicodeText, nullable=False)
    filename = Column(UnicodeText, nullable=False)
    url_download = Column(UnicodeText, nullable=False)
    public_comment = Column(UnicodeText)
    fps = Column(Float)
    frame_count = Column(Integer)
    duration = Column(Float)
    width = Column(Integer)
    height = Column(Integer)
    is_enabled = Column(Boolean, index=True, server_default='1')
    is_finished = Column(Boolean, index=True)
    allowed_annotation_object_types = Column(Unicode(255), nullable=False)
    options = Column(UnicodeText)

    uploader_id = Column(Integer, ForeignKey('annotators.id'), nullable=False)
    uploader = relationship('Annotator', backref='uploaded_videos')

    annotators = relationship('Annotator',
                              secondary=table_bind_video_to_annotator,
                              backref='videos')

    logger.debug('Initialized Video')

    def __repr__(self):
        return "<Video#%s(%s,%s,%s,%s)>" % (str(self.id), unicode(self.name).encode('utf8'), unicode(self.filename).encode('utf8'), 'enabled' if self.is_enabled else 'disabled', 'finished' if self.is_finished else 'not finished')

    def get_option(self, key=[], use_defaults=True):
        try:
            entity_options = json.loads(self.options)
        except:
            entity_options = {}

        if use_defaults:
            options = util.dict_merge(default_options, entity_options)
        else:
            options = entity_options

        if isinstance(key, basestring):
            key = key.split('.')

        for k in key:
            options = options[k]

        return options

    def annotation_objects_all(self):
        """
        Returns all annotation objects related to this video, with object's first and last frame.
        Annotation objects are sorted by the time of theirs first occurrence in the video.

        :rtype: list of (AnnotationObject, int, int)
        """

        q = database.db.session.query(AnnotationObject, func.min(AnnotationValue.frame_from), func.max(AnnotationValue.frame_from))
        q = q.filter_by(video_id=self.id)
        q = q.join(AnnotationObject.annotation_values)
        q = q.group_by(AnnotationObject.id)
        q = q.order_by(func.min(AnnotationValue.frame_from), func.max(AnnotationValue.frame_from), AnnotationObject.id)

        return q.all()

    def annotation_objects_in_frame(self, frame):
        """
        Returns annotation objects related to this video that are visible in given time.
        AnnotationValues are lazily-loaded, in comparison to annotation_objects_in_frame_intervals()

        SQL:
            SELECT annotation_objects....., min(annotation_values.frame_from) AS min_1, max(annotation_values.frame_from) AS max_1
            FROM annotation_objects
            INNER JOIN annotation_values ON annotation_objects.id = annotation_values.annotation_object_id
            WHERE annotation_objects.video_id = %s
            GROUP BY annotation_objects.id
            HAVING min(annotation_values.frame_from) <= %s AND max(annotation_values.frame_from) >= %s
            ORDER BY min(annotation_values.frame_from), max(annotation_values.frame_from), annotation_objects.id

        :rtype: list of (AnnotationObject, int, int)
        """

        q = database.db.session.query(AnnotationObject, func.min(AnnotationValue.frame_from), func.max(AnnotationValue.frame_from))
        q = q.filter_by(video_id=self.id)
        q = q.join(AnnotationObject.annotation_values)
        q = q.group_by(AnnotationObject.id)
        q = q.having((func.min(AnnotationValue.frame_from) <= frame) & (func.max(AnnotationValue.frame_from) >= frame))
        q = q.order_by(func.min(AnnotationValue.frame_from), func.max(AnnotationValue.frame_from), AnnotationObject.id)
        q = q.all()

        return q

    def annotation_objects_in_frame_intervals(self, intervals, filter_object_ids=None):
        """
        Returns annotation objects related to this video that are visible in given time intervals <from, to>
        Related AnnotationValues collections are eagerly loaded from database (not lazily which is the default).

        Optionally with filter_object_ids, only AnnotationObjects with given IDs are returned.

        :param filter_object_ids: list of AnnotationObject ids
        :type filter_object_ids: list of int
        :param intervals: list of tuples each representing one time interval (frame_from, frame_to)
        :type intervals: list of (int, int)
        :rtype: list of (AnnotationObject, int, int)
        """

        if not len(intervals):
            return []

        q = database.db.session.query(AnnotationObject, func.min(AnnotationValue.frame_from), func.max(AnnotationValue.frame_from))
        q = q.filter_by(video_id=self.id)
        q = q.join(AnnotationObject.annotation_values)

        if filter_object_ids is not None:
            q = q.filter(AnnotationObject.id.in_(filter_object_ids))

        q = q.options(subqueryload(AnnotationObject.annotation_values)) # eagerly load "annotation_values" relation
        q = q.group_by(AnnotationObject.id)

        having = None

        # construct having condition
        for frame_from, frame_to in intervals:
            h = (func.min(AnnotationValue.frame_from) <= frame_to) & (func.max(AnnotationValue.frame_from) >= frame_from)
            having = h if having is None else having | h

        q = q.having(having)

        q = q.order_by(func.min(AnnotationValue.frame_from), func.max(AnnotationValue.frame_from), AnnotationObject.id)
        q = q.all()

        return q

    def annotation_object_next(self, current_frame, current_annotation_object=None, to_future=True):
        """
        When current_annotation_object is None, nearest AnnotationObject in the future (in respect to current_frame) is returned.
        With current_annotation_object given, "next" AnnotationObject is returned, i.e. an object with higher ID in the current frame
        or the nearest in the future.

        If to_future is false, the search is done in the past instead of the future.

        Returned tuple contains the next object and its starting and ending frame.

        :rtype: (AnnotationObject, int, int)
        """

        q = database.db.session.query(AnnotationObject, func.min(AnnotationValue.frame_from), func.max(AnnotationValue.frame_from))
        q = q.filter_by(video_id=self.id)
        q = q.join(AnnotationObject.annotation_values)
        q = q.group_by(AnnotationObject.id)

        if to_future:
            if current_annotation_object is None:
                # nearest AnnotationObject in future
                q = q.having(func.min(AnnotationValue.frame_from) > current_frame)
                q = q.order_by(func.min(AnnotationValue.frame_from), AnnotationObject.id)
            else:
                # nearest AnnotationObject in future, or in the same frame with bigger ID
                current_id = current_annotation_object.id
                q = q.having( (func.min(AnnotationValue.frame_from) > current_frame) |
                              ((AnnotationObject.id > current_id) & (func.min(AnnotationValue.frame_from) <= current_frame) & (func.max(AnnotationValue.frame_from) >= current_frame))
                            )
                q = q.order_by(func.min(AnnotationValue.frame_from), AnnotationObject.id)
        else:
            if current_annotation_object is None:
                # nearest AnnotationObject in past
                q = q.having(func.max(AnnotationValue.frame_from) < current_frame)
                q = q.order_by(desc(func.max(AnnotationValue.frame_from)), desc(AnnotationObject.id))
            else:
                # nearest AnnotationObject in past, or in the same frame with lower ID
                current_id = current_annotation_object.id
                q = q.having( (func.max(AnnotationValue.frame_from) < current_frame) |
                              ((AnnotationObject.id < current_id) & (func.min(AnnotationValue.frame_from) <= current_frame) & (func.max(AnnotationValue.frame_from) >= current_frame))
                            )
                q = q.order_by(desc(func.max(AnnotationValue.frame_from)), desc(AnnotationObject.id))

        q = q.limit(1)
        q = q.all()

        if len(q) < 1:
            return None

        if len(q) > 1:
            raise Exception('Returned collection cannot contain more than 1 item.')

        return q[0]

    def annotation_object_previous(self, current_frame, current_annotation_object=None):
        """
        Shortcut for annotation_object_next() with to_future=False
        """

        return self.annotation_object_next(current_frame, current_annotation_object, to_future=False)

    def import_annotations(self, data, annotator=None, fast_database_inserts=True):
        """
        Import AnnotationObject and AnnotationValue objects for this video.
        Returns list of newly created antities.

        fast_database_inserts - when enabled, AnnotationValue entities are not created and data are directly inserted into database
                              - speedup about 20%

        Example of input data (list of annotation objects, which have related annotation values):
            [
                {
                    "type": "rectangle",                                    ### REQUIRED
                    "public_comment": "Another white player",
                    "annotation_values": [                                  ### REQUIRED
                        ["position_rectangle", 0, [120, 173, 128, 190]],
                        ["position_rectangle", 30, [124, 175, 131, 189]],
                        ["football_identity_1", "white player"],
                        ["football_activity_1", 0, "walking"]
                    ]
                }
            ]

        """

        entities = []

        annotation_attributes_cache = {}

        t0 = time.time()

        for i, data_object in enumerate(data):
            logger.info("Importing annotation object %4d/%4d with %4d values. (%1.2f objects/s)" % (i, len(data), len(data_object['annotation_values']), i/(time.time()-t0) if i>0 else 0))

            # create new AnnotationObject
            annotation_object = AnnotationObject(type=data_object['type'], created_by=annotator, modified_by=annotator, video=self)

            if 'public_comment' in data_object:
                annotation_object.public_comment = data_object['public_comment']

            entities.append(annotation_object)
            database.db.session.add(annotation_object)

            if fast_database_inserts:
                # we need to generate new annotation_object.id
                database.db.session.flush()

            # create new AnnotationValue objects
            annotation_values = []

            for data_av in data_object['annotation_values']:
                # find annotation attribute
                aa_id = data_av[0]

                if not aa_id in annotation_attributes_cache:
                    annotation_attributes_cache[aa_id] = repository.annotation_attributes.get_one_by_name(aa_id)

                annotation_attribute = annotation_attributes_cache[aa_id]

                # import annotation value
                if fast_database_inserts:
                    # "fast" insert - do not create entities, directly insert into database
                    # see http://stackoverflow.com/questions/11769366/why-is-sqlalchemy-insert-with-sqlite-25-times-slower-than-using-sqlite3-directly

                    data_type = annotation_attribute.data_type

                    annotation_values.append({
                             'annotation_attribute_id': annotation_attribute.id,
                             'annotation_object_id': annotation_object.id,
                             'created_by_id': annotator.id if annotator is not None else None,
                             'frame_from': None if annotation_attribute.is_global else data_av[1],
                             'value': AnnotationValue.encode_value(data_av[1 if annotation_attribute.is_global else 2], data_type)
                    })
                else:
                    # "slow" insert - create entity
                    annotation_value = AnnotationValue(annotation_attribute=annotation_attribute, annotation_object=annotation_object, created_by=annotator)

                    if annotation_attribute.is_global:
                        annotation_value.value = data_av[1]
                    else:
                        annotation_value.frame_from = data_av[1]
                        annotation_value.value = data_av[2]

                    entities.append(annotation_value)

            if fast_database_inserts:
                database.db.session.execute(
                    AnnotationValue.__table__.insert(),
                    annotation_values
                )
            else:
                database.db.session.flush()

        return entities


table_bind_video_to_annotation_attributes = Table('bind_video_to_annotation_attributes', Base.metadata,
                                                  Column('video_id', Integer, ForeignKey('videos.id', ondelete='CASCADE')),
                                                  Column('annotation_attribute_id', Integer, ForeignKey('annotation_attributes.id'))
)


class AnnotationAttribute(Base):
    """
    Allowed annotation attributes for videos.
    It is a list of all possible annotation attributes that can by annotated for all videos. Only a subset can be selected for one video. Annotated values are then stored in "annotation_attributes" table.
    """

    __tablename__ = 'annotation_attributes'

    id = Column(Integer, primary_key=True)

    name = Column(Unicode(255), nullable=False)
    is_global = Column(Boolean, index=True)
    description = Column(UnicodeText)
    data_type = Column(Unicode(255), nullable=False)
    _allowed_values = Column('allowed_values', UnicodeText)
    annotation_object_type = Column(Unicode(255), nullable=False)
    options = Column(UnicodeText)

    videos = relationship('Video',
                          secondary=table_bind_video_to_annotation_attributes,
                          backref='annotation_attributes')

    allowed_values = synonym('_allowed_values') #, descriptor=allowed_values)

    logger.debug('Initialized AnnotationAttribute')

    @property
    def allowed_values(self):
        if self._allowed_values is None:
            return None

        # sometimes it is str
        avs = unicode(self._allowed_values)

        return avs.split('|')

    @allowed_values.setter
    def allowed_values(self, value):
        if isinstance(value, (list, tuple)):
            value = u'|'.join(value)

        self._allowed_values = value

    def __repr__(self):
        return "<AnnotationAttribute#%s(%s,%s)>" % (str(self.id), unicode(self.name).encode('utf8'), 'global' if self.is_global else 'local')

    def get_option(self, key=[], use_defaults=True):
        try:
            entity_options = json.loads(self.options)
        except:
            entity_options = {}

        if use_defaults:
            options = util.dict_merge(default_options, entity_options)
        else:
            options = entity_options

        if isinstance(key, basestring):
            key = key.split('.')

        for k in key:
            options = options[k]

        return options

    def autocomplete_values(self, text=None):
        value_like = None

        if text is not None:
            value_like = '%'+text+'%'

        avs = repository.annotation_values.search(annotation_attribute_id=self.id, value_like=value_like, limit=700, group_by_value=True)

        result = []

        if len(avs) >= 700:
            # too many values, return nothing
            return result

        for av in avs:
            result.append(unicode(av.value))

        return result

class AnnotationObject(Base):
    """
    Annotation object associated to a video, it serves as a container for annotation attributes.
    """

    __tablename__ = 'annotation_objects'

    id = Column(Integer, primary_key=True)

    _type = Column('type', Unicode(255), nullable=False)
    public_comment = Column(UnicodeText)
    is_verified = Column(Boolean, index=True)
    is_editable = Column(Boolean, server_default='1')
    options = Column(UnicodeText)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    modified_at = Column(TIMESTAMP, onupdate=func.current_timestamp())

    created_by_id = Column(Integer, ForeignKey('annotators.id'))
    created_by = relationship('Annotator', backref='annotation_objects_created', foreign_keys=[created_by_id])

    modified_by_id = Column(Integer, ForeignKey('annotators.id'))
    modified_by = relationship('Annotator', backref='annotation_objects_modified', foreign_keys=[modified_by_id])

    video_id = Column(Integer, ForeignKey('videos.id', ondelete='CASCADE'), nullable=False)
    video = relationship('Video', backref=backref("annotation_objects", cascade="all, delete-orphan", passive_deletes=True))

    type = synonym('_type') #, descriptor=type)

    allowed_annotation_types = ['rectangle', 'circle', 'point', 'nonvisual']

    logger.debug('Initialized AnnotationObject')

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, value):
        if value is not None:
            if value not in self.allowed_annotation_types:
                raise Exception('Unsupported annotation type: %s' % (value))

        self._type = value

    def __repr__(self):
        return "<AnnotationObject#%s(%s,video %s,%s)>" % (str(self.id), unicode(self.type).encode('utf8'), str(self.video_id), 'editable' if self.is_editable else 'not editable')

    def get_text(self, frame=None):
        """
        Returns text representation of the object (global and local attributes separately in a tuple), suitable for the user.
        Text is composed from all annotation values which are visible in given frame.

        :rtype: (unicode,unicode)
        """

        text = {'global': [], 'local': []}

        for av in self.annotation_values_global():
            s = av.get_text()

            if s is not None:
                text['global'].append(s)

        if frame is not None:
            for av in self.annotation_values_local_interpolate_in_frame(frame):
                s = av.get_text()

                if s is not None:
                    text['local'].append(s)

        return u", ".join(text['global']), u", ".join(text['local'])

    def get_option(self, key=[], use_defaults=True):
        if use_defaults:
            options = default_options
        else:
            options = {}

        if self.video is not None:
            options = util.dict_merge(options, self.video.get_option(use_defaults=False))

        try:
            entity_options = json.loads(self.options)
        except:
            entity_options = {}

        options = util.dict_merge(options, entity_options)

        if isinstance(key, basestring):
            key = key.split('.')

        for k in key:
            options = options[k]

        return options

    def annotation_values_global(self):
        """
        Returns list of all GLOBAL annotation values associated to this annotation
        :rtype: list of AnnotationValue
        """

        result = []

        for annotation_value in self.annotation_values:
            if annotation_value.annotation_attribute.is_global:
                result.append(annotation_value)

        return result

    def annotation_values_local(self, ignore_interpolated=True):
        """
        Returns list of all LOCAL annotation values associated to this annotation object
        :rtype: list of AnnotationValue
        """

        result = []

        for annotation_value in self.annotation_values:
            if not annotation_value.annotation_attribute.is_global:
                if not ignore_interpolated or not annotation_value.is_interpolated:
                    result.append(annotation_value)

        return result

    def annotation_values_local_grouped(self):
        """
        Returns list of all LOCAL annotation values associated to this annotation object, grouped into dict by annotation attributes
        :rtype: dict of AnnotationAttribute.id => list of AnnotationValue
        """
        avsg = defaultdict(list)

        # ruzne atributy
        for av in self.annotation_values_local():
            aa = av.annotation_attribute

            if aa is None:
                raise Exception('Annotation attribute cannot be None')

            avsg[aa.id].append(av)

        return avsg

    def annotation_values_local_interpolate_in_frame(self, frame, interpolation=True):
        """
        Returns list of LOCAL annotation values for given frame.
        Annotation values are interpolated when the annotation values are not specified exactly for given frame
        Interpolated values are newly created AnnotationValue instances with is_interpolated attribute set to True
        Newly created AnnotationValue instances are automatically expunged from sqlalchemy session, not to be persisted in the database.

        :rtype: list of AnnotationValue
        """

        result = []

        for annotation_attribute_id, annotation_values in self.annotation_values_local_grouped().iteritems():
            # interpolate each annotation attribute separately

            # at first, try to find annotation value in the given frame (no interpolation needed)
            exact_match_av = None

            for av in annotation_values:
                if av.frame_from == frame:
                    # found exact match
                    if exact_match_av is not None:
                        raise Exception('Two local annotation values found in the same frame! (IDs: %d, %d)' % (
                            av.id, exact_match_av.id))

                    exact_match_av = av

            if exact_match_av is not None:
                result.append(exact_match_av)
                continue

            # no annotation value was found in the given frame, interpolation is needed

            if not interpolation:
                continue

            # find two nearest annotation values, one past and one future
            nearest_av_before = None
            nearest_av_after = None

            for av in annotation_values:
                if av.frame_from < frame:
                    if nearest_av_before is None or nearest_av_before.frame_from < av.frame_from:
                        nearest_av_before = av
                elif av.frame_from > frame:
                    if nearest_av_after is None or nearest_av_after.frame_from > av.frame_from:
                        nearest_av_after = av

            if nearest_av_before is None and nearest_av_after is None:
                raise Exception('No annotation values were found in the past and future!?!')

            av_interpolated = AnnotationValue.interpolate(nearest_av_before, nearest_av_after, frame)

            if av_interpolated is not None:
                result.append(av_interpolated)
                continue

        return result

    def active_interval(self):
        """
        Return frame interval, where this object is active (i.e. has some annotation values or some annotation values can be interpolated)

        :rtype: (frame_from, frame_to)
        """

        frame_from = None
        frame_to = None

        for av in self.annotation_values_local():
            frame = av.frame_from

            if frame_from is None or frame_from > frame:
                frame_from = frame

            if frame_to is None or frame_to < frame:
                frame_to = frame

        return frame_from, frame_to

    def is_active_in_frame(self, frame):
        """
        Returns True if this object is active in given frame, see active_interval()

        :rtype: bool
        """

        active_interval = self.active_interval()

        if None in active_interval:
            return False

        frame_from, frame_to = active_interval

        return frame_from <= frame <= frame_to

class AnnotationValue(Base):
    """
    Annotation value associated to "annotation object" container.
    """

    __tablename__ = 'annotation_values'

    is_interpolated = False

    id = Column(Integer, primary_key=True)
    options = Column(UnicodeText)

    frame_from = Column(Integer, index=True)
    _value = Column('value', UnicodeText)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    modified_at = Column(TIMESTAMP, onupdate=func.current_timestamp())

    created_by_id = Column(Integer, ForeignKey('annotators.id'))
    created_by = relationship('Annotator', backref='annotation_values_created', foreign_keys=[created_by_id])

    modified_by_id = Column(Integer, ForeignKey('annotators.id'))
    modified_by = relationship('Annotator', backref='annotation_values_modified', foreign_keys=[modified_by_id])

    annotation_attribute_id = Column(Integer, ForeignKey('annotation_attributes.id'), nullable=False)
    annotation_attribute = relationship('AnnotationAttribute', backref='annotation_values')

    annotation_object_id = Column(Integer, ForeignKey('annotation_objects.id', ondelete='CASCADE'), nullable=False)
    annotation_object = relationship('AnnotationObject', backref=backref('annotation_values', cascade="all, delete-orphan", passive_deletes=True))

    value = synonym('_value') #, descriptor=value)

    logger.debug('Initialized AnnotationValue')

    @property
    def value(self):
        # decode value from string
        if self.annotation_attribute is None:
            raise Exception('annotation_attribute cannot be None')

        self.check_consistency()

        data_type = self.annotation_attribute.data_type

        return self.decode_value(self._value, data_type)

    @value.setter
    def value(self, v):
        # encode value into string that will be stored in database
        if self.annotation_attribute is None:
            raise Exception('annotation_attribute cannot be None')

        self.check_consistency()

        data_type = self.annotation_attribute.data_type

        v = self.encode_value(v, data_type)

        allowed_values = self.annotation_attribute.allowed_values

        if allowed_values is not None:
            if v not in allowed_values:
                raise Exception('Value "%s" is not allowed (%s)' % (v, allowed_values))

        self._value = v

    def __repr__(self):
        return "<AnnotationValue#%s(frame %s,%s,%s)>" % (str(self.id), str(self.frame_from), unicode(self._value).encode('utf8'), 'interpolated' if self.is_interpolated else 'not interpolated')

    def get_text(self):
        """
        Returns text representation of the annotation value, suitable for the user.
        """

        if self.annotation_attribute is None:
            return None

        # no text for positional attributes
        if self.annotation_attribute.name.startswith('position_'):
            return None

        data_type = self.annotation_attribute.data_type

        if data_type == u'bool':
            text = self.annotation_attribute.name if self._value else None
        elif data_type in [u'int', u'float']:
            text = self.annotation_attribute.name + '=' + unicode(self._value)
        elif data_type == u'unicode':
            text = self._value
        else:
            text = None

        return text

    @classmethod
    def encode_value(cls, v, data_type):
        if data_type in [u'int', u'float']:
            s = unicode(v)
        elif data_type == u'bool':
            s = u'1' if v else u'0'
        elif data_type == u'unicode':
            s = v
        elif data_type == u'position_rectangle':
            # sort x and y coordinates
            v = (min(v[0], v[2]), min(v[1], v[3]), max(v[0], v[2]), max(v[1], v[3]))
            s = u'%d,%d,%d,%d' % (v[0], v[1], v[2], v[3])
        elif data_type == u'position_circle':
            s = u'%d,%d,%.2f' % (v[0], v[1], v[2])
        elif data_type == u'position_point':
            s = u'%d,%d' % (v[0], v[1])
        elif data_type == u'position_nonvisual':
            s = u''
        else:
            raise Exception('Unsupported data_type: %s' % (data_type))

        return s

    @classmethod
    def decode_value(cls, s, data_type):
        if data_type == u'int':
            v = int(s)
        elif data_type == u'float':
            v = float(s)
        elif data_type == u'bool':
            v = bool(int(s))
        elif data_type == u'unicode':
            v = s
        elif data_type == u'position_rectangle':
            v = s.split(',')
            v = (int(v[0]), int(v[1]), int(v[2]), int(v[3]))
        elif data_type == u'position_circle':
            v = s.split(',')
            v = (int(v[0]), int(v[1]), float(v[2]))
        elif data_type == u'position_point':
            v = s.split(',')
            v = (int(v[0]), int(v[1]))
        elif data_type == u'position_nonvisual':
            # value is not used here
            v = None
        else:
            raise Exception('Unsupported data_type: %s' % (data_type))

        return v

    @classmethod
    def interpolate_float(cls, point1, point2, x):
        """
        Linear interpolation - estimate y value in position x for given two points
        """

        if point1 is None and point2 is None:
            return None

        if point1 is None or point2 is None:
            return point1[1] if point1 is not None else point2[1]

        return (float(point2[1]) - point1[1]) / (point2[0] - point1[0]) * (x - point1[0]) + point1[1]

    @classmethod
    def interpolate(cls, annotation_value_before, annotation_value_after, frame):
        """
        Returns new AnnotationValue, with value interpolated in given frame, from one or two existing annotation values.
        Newly created object is automatically expunged from sqlalchemy session, not to be persisted in the database.

        :rtype: AnnotationValue
        """

        if annotation_value_before is not None and annotation_value_after is not None:
            if annotation_value_before.annotation_attribute != annotation_value_after.annotation_attribute:
                raise Exception(
                    "annotation_value_before and annotation_value_after must have same annotation_attribute")
            if annotation_value_before.annotation_object != annotation_value_after.annotation_object:
                raise Exception("annotation_value_before and annotation_value_after must have same annotation_object")

        if annotation_value_before is not None and annotation_value_before.frame_from > frame:
            raise Exception("Cannot interpolate: frame is lower than annotation_value_before.frame_from (%d, %d)" % (
                frame, annotation_value_before.frame_from))

        if annotation_value_after is not None and annotation_value_after.frame_from < frame:
            raise Exception("Cannot interpolate: frame is higher than annotation_value_after.frame_from (%d, %d)" % (
                frame, annotation_value_after.frame_from))

        # from where to copy attributes
        av_first = annotation_value_before if annotation_value_before is not None else annotation_value_after

        # create new AnnotationValue with interpolated values
        av_interpolated = AnnotationValue()
        av_interpolated.is_interpolated = True
        av_interpolated.frame_from = frame
        av_interpolated.annotation_attribute = av_first.annotation_attribute
        av_interpolated.annotation_attribute_id = av_first.annotation_attribute_id
        av_interpolated.annotation_object = av_first.annotation_object
        av_interpolated.annotation_object_id = av_first.annotation_object_id

        # expunge object - do not persist this object in database
        av_interpolated.database_session_remove()

        data_type = av_first.annotation_attribute.data_type

        t1 = annotation_value_before.frame_from if annotation_value_before is not None else None
        t2 = annotation_value_after.frame_from if annotation_value_after is not None else None

        if annotation_value_before is None and annotation_value_after is None and data_type != u'position_nonvisual':
            raise Exception("Both annotation values cannot be None for data type: %s" % (data_type))

        # interpolate value, each data type has own method
        if data_type == u'int' or data_type == u'float':
            if t1 is None or t2 is None:
                # one value is None, use the second value as a result
                av_interpolated.value = av_first.value
            else:
                # both values are set, interpolate result value
                v = cls.interpolate_float((t1, annotation_value_before.value),
                                          (t2, float(annotation_value_after.value)))
                if data_type == u'int':
                    v = int(v)
                av_interpolated.value = v
        elif data_type == u'bool' or data_type == u'unicode':
            # result value is same as the "before" value, "after" value is ignored
            if t1 is None:
                return None
            av_interpolated.value = annotation_value_before.value
        elif data_type == u'position_rectangle':
            if t1 is None or t2 is None:
                # one value is None, use the second value as a result
                av_interpolated.value = av_first.value
            else:
                # both values are set, interpolate result value
                x1 = int(cls.interpolate_float((t1, annotation_value_before.value[0]), (t2, annotation_value_after.value[0]), frame))
                y1 = int(cls.interpolate_float((t1, annotation_value_before.value[1]), (t2, annotation_value_after.value[1]), frame))
                x2 = int(cls.interpolate_float((t1, annotation_value_before.value[2]), (t2, annotation_value_after.value[2]), frame))
                y2 = int(cls.interpolate_float((t1, annotation_value_before.value[3]), (t2, annotation_value_after.value[3]), frame))
                av_interpolated.value = [x1, y1, x2, y2]
        elif data_type == u'position_circle':
            if t1 is None or t2 is None:
                # one value is None, use the second value as a result
                av_interpolated.value = av_first.value
            else:
                # both values are set, interpolate result value
                x = int(cls.interpolate_float((t1, annotation_value_before.value[0]), (t2, annotation_value_after.value[0]), frame))
                y = int(cls.interpolate_float((t1, annotation_value_before.value[1]), (t2, annotation_value_after.value[1]), frame))
                r = cls.interpolate_float((t1, annotation_value_before.value[2]), (t2, annotation_value_after.value[2]), frame)
                av_interpolated.value = [x, y, r]
        elif data_type == u'position_point':
            if t1 is None or t2 is None:
                # one value is None, use the second value as a result
                av_interpolated.value = av_first.value
            else:
                # both values are set, interpolate result value
                x = int(cls.interpolate_float((t1, annotation_value_before.value[0]), (t2, annotation_value_after.value[0]), frame))
                y = int(cls.interpolate_float((t1, annotation_value_before.value[1]), (t2, annotation_value_after.value[1]), frame))
                av_interpolated.value = [x, y]
        elif data_type == u'position_nonvisual':
            av_interpolated.value = None
        else:
            raise Exception('Unsupported data_type for interpolation: %s' % (data_type))

        return av_interpolated

    def get_option(self, key=[], current_annotator=None, use_defaults=True):
        """
        Key: list of keys (e.g. 'gui', 'color', 'annotation_object']) or string (e.g. 'gui.color.annotation_object')

        options are merged from (in this order):
            1) default_options
            2) annotator's options
            3) annotation object (which inherits options from video)
            4) annotation attribute
            5) self.options
        """

        if use_defaults:
            options = default_options
        else:
            options = {}

        if current_annotator is not None:
            options = util.dict_merge(options, current_annotator.get_option(use_defaults=False))
        if self.annotation_attribute is not None:
            options = util.dict_merge(options, self.annotation_attribute.get_option(use_defaults=False))
        if self.annotation_object is not None:
            options = util.dict_merge(options, self.annotation_object.get_option(use_defaults=False))

        try:
            entity_options = json.loads(self.options)
        except:
            entity_options = {}

        options = util.dict_merge(options, entity_options)

        if isinstance(key, basestring):
            key = key.split('.')

        for k in key:
            options = options[k]

        return options

    def check_consistency(self):
        if self.annotation_object and self.annotation_attribute:
            if self.annotation_object.type != self.annotation_attribute.annotation_object_type:
                raise Exception(
                    "Annotation object type and annotation attribute's annotation object type mismatch (%s, %s)" % (
                        self.annotation_object.type, self.annotation_attribute.annotation_object_type))

    def database_session_remove(self):
        # do not persist this object in database
        database.db.session.expunge(self)
        sqlalchemy.orm.session.make_transient(self)

    def database_session_add(self, disable_is_interpolated_flag=True):
        # persist this object in database
        if disable_is_interpolated_flag:
            self.is_interpolated = False
        database.db.session.add(self)


class Log(Base):
    """
    Logging data
    """

    __tablename__ = 'logs'

    id = Column(Integer, primary_key=True)

    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

    created_by_id = Column(Integer, ForeignKey('annotators.id'))
    created_by = relationship('Annotator', backref='logs_created', foreign_keys=[created_by_id])

    execution_number = Column(Integer)

    type = Column(Unicode(255), nullable=False, index=True)
    value = Column(UnicodeText)

    logger.debug('Initialized Log')

    def __repr__(self):
        return "<Log#%s(%s)>" % (str(self.id), unicode(self.type).encode('utf8'))
