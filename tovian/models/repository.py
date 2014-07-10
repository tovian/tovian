# -*- coding: utf-8 -*-

"""
    Repository - interface for querying data
"""

__version__ = "$Id: repository.py 355 2014-04-15 11:44:14Z campr $"


import entity
import database
import sqlalchemy
import logging
import datetime
import json

logger = logging.getLogger(__name__)
logger.debug('Import ' + __name__)


class Annotators():
    def get_all(self):
        """
        :rtype: list of entity.Annotator
        """

        q = database.db.session.query(entity.Annotator)

        return q.all()

    def get_all_enabled(self):
        """
        :rtype: list of entity.Annotator
        """

        q = database.db.session.query(entity.Annotator)
        q = q.filter_by(is_enabled=True)

        return q.all()

    def get_one(self, email_name_id):
        """
        Try to find one user by email, name or ID

        :rtype: entity.Annotator or None
        """

        try:
            o = self.get_one_by_email(unicode(email_name_id))

            if o:
                return o
        except:
            pass

        try:
            o = self.get_one_by_name(unicode(email_name_id))

            if o:
                return o
        except:
            pass

        try:
            o = self.get_one_by_id(int(email_name_id))

            if o:
                return o
        except:
            pass

        return None

    def get_one_by_id(self, id):
        """
        :rtype: entity.Annotator or None
        """

        try:
            q = database.db.session.query(entity.Annotator)
            q = q.filter_by(id=id)

            return q.one()

        except sqlalchemy.orm.exc.NoResultFound, sqlalchemy.orm.exc.MultipleResultsFound:
            return None

    def get_one_by_name(self, name):
        """
        :rtype: entity.Annotator or None
        """

        try:
            q = database.db.session.query(entity.Annotator)
            q = q.filter_by(name=name)

            return q.one()

        except sqlalchemy.orm.exc.NoResultFound, sqlalchemy.orm.exc.MultipleResultsFound:
            return None

    def get_one_by_email(self, email):
        """
        :rtype: entity.Annotator or None
        """

        try:
            q = database.db.session.query(entity.Annotator)
            q = q.filter_by(email=email)

            return q.one()

        except sqlalchemy.orm.exc.NoResultFound, sqlalchemy.orm.exc.MultipleResultsFound:
            return None

    def get_one_enabled_by_name(self, name):
        """
        :rtype: entity.Annotator or None
        """

        try:
            q = database.db.session.query(entity.Annotator)
            q = q.filter_by(name=name, is_enabled=True)

            return q.one()

        except sqlalchemy.orm.exc.NoResultFound, sqlalchemy.orm.exc.MultipleResultsFound:
            return None

    def get_one_enabled_by_name_and_password(self, name, password):
        """
        Returns one enabled annotator by name and password

        :rtype: entity.Annotator or None
        """

        annotator = self.get_one_enabled_by_name(name)

        if not annotator:
            return None

        if annotator.match_password(password):
            return annotator

        return None

    def get_one_enabled_by_email(self, email):
        """
        :rtype: entity.Annotator or None
        """

        try:
            q = database.db.session.query(entity.Annotator)
            q = q.filter_by(email=email, is_enabled=True)

            return q.one()

        except sqlalchemy.orm.exc.NoResultFound, sqlalchemy.orm.exc.MultipleResultsFound:
            return None

    def get_one_enabled_by_email_and_password(self, email, password):
        """
        Returns one enabled annotator by email and password

        :rtype: entity.Annotator or None
        """

        annotator = self.get_one_enabled_by_email(email)

        if not annotator:
            return None

        if annotator.match_password(password):
            return annotator

        return None


class Videos():
    def get_all(self):
        """
        :rtype: list of entity.Video
        """

        q = database.db.session.query(entity.Video)

        return q.all()

    def get_one(self, filename_name_id):
        """
        Try to find one video by filename, name or ID

        :rtype: entity.Video or None
        """

        try:
            o = self.get_one_by_filename(unicode(filename_name_id))

            if o:
                return o #or self.get_one_by_name(unicode(filename_name_id)) or self.get_one_by_id(int(filename_name_id))
        except:
            pass

        try:
            o = self.get_one_by_name(unicode(filename_name_id))

            if o:
                return o
        except:
            pass

        try:
            o = self.get_one_by_id(unicode(filename_name_id))

            if o:
                return o
        except:
            pass

        return None

    def get_one_by_id(self, id):
        """
        :rtype: entity.Video or None
        """

        try:
            q = database.db.session.query(entity.Video)
            q = q.filter_by(id=id)

            return q.one()

        except sqlalchemy.orm.exc.NoResultFound, sqlalchemy.orm.exc.MultipleResultsFound:
            return None

    def get_one_by_name(self, name):
        """
        :rtype: entity.Video or None
        """

        try:
            q = database.db.session.query(entity.Video)
            q = q.filter_by(name=name)

            return q.one()

        except sqlalchemy.orm.exc.NoResultFound, sqlalchemy.orm.exc.MultipleResultsFound:
            return None

    def get_one_by_filename(self, filename):
        """
        :rtype: entity.Video or None
        """

        try:
            q = database.db.session.query(entity.Video)
            q = q.filter_by(filename=filename)

            return q.one()

        except sqlalchemy.orm.exc.NoResultFound, sqlalchemy.orm.exc.MultipleResultsFound:
            return None


class AnnotationObjects():
    def get_all(self):
        """
        :rtype: list of entity.AnnotationObject
        """

        q = database.db.session.query(entity.AnnotationObject)

        return q.all()

    def get_one_by_id(self, id):
        """
        :rtype: entity.AnnotationObject or None
        """

        try:
            q = database.db.session.query(entity.AnnotationObject)
            q = q.filter_by(id=id)

            return q.one()

        except sqlalchemy.orm.exc.NoResultFound, sqlalchemy.orm.exc.MultipleResultsFound:
            return None


class AnnotationAttributes():
    def get_all(self):
        """
        :rtype: list of entity.AnnotationAttribute
        """

        q = database.db.session.query(entity.AnnotationAttribute)

        return q.all()

    def get_one(self, name_id):
        """
        Try to find one attribute by name or ID

        :rtype: entity.AnnotationAttribute or None
        """

        try:
            o = self.get_one_by_name(unicode(name_id))

            if o:
                return o
        except:
            pass

        try:
            o = self.get_one_by_id(int(name_id))

            if o:
                return o
        except:
            pass

        return None

    def get_one_by_id(self, id):
        """
        :rtype: entity.AnnotationAttribute or None
        """

        try:
            q = database.db.session.query(entity.AnnotationAttribute)
            q = q.filter_by(id=id)

            return q.one()

        except sqlalchemy.orm.exc.NoResultFound, sqlalchemy.orm.exc.MultipleResultsFound:
            return None

    def get_one_by_name(self, name):
        """
        :rtype: entity.AnnotationAttribute or None
        """

        try:
            q = database.db.session.query(entity.AnnotationAttribute)
            q = q.filter_by(name=name)

            return q.one()

        except sqlalchemy.orm.exc.NoResultFound, sqlalchemy.orm.exc.MultipleResultsFound:
            return None


class AnnotationValues():
    def get_one_by_id(self, id):
        """
        :rtype: entity.AnnotationValue or None
        """

        try:
            q = database.db.session.query(entity.AnnotationValue)
            q = q.filter_by(id=id)

            return q.one()

        except sqlalchemy.orm.exc.NoResultFound, sqlalchemy.orm.exc.MultipleResultsFound:
            return None

    def get_all(self):
        """
        :rtype: list of entity.AnnotationValue
        """

        q = database.db.session.query(entity.AnnotationValue)

        return q.all()

    def search(self, annotation_attribute_id=None, value_like=None, limit=None, group_by_value=False):
        """
        :rtype: list of entity.Annotator
        """

        q = database.db.session.query(entity.AnnotationValue)

        if annotation_attribute_id is not None:
            q = q.filter_by(annotation_attribute_id=annotation_attribute_id)

        if value_like is not None:
            q = q.filter(entity.AnnotationValue._value.like(value_like))

        if group_by_value:
            q = q.group_by(entity.AnnotationValue._value)

        q = q.order_by(entity.AnnotationValue._value)

        if limit is not None:
            q = q.limit(limit)

        return q.all()


class Logs():
    execution_number = None

    def get_by_annotator(self, annotator):
        """
        :rtype: list of entity.Log
        """

        if type(annotator) is int or type(annotator) is long:
            annotator_id = annotator
        else:
            annotator_id = annotator.id

        q = database.db.session.query(entity.Log)
        q = q.filter_by(created_by_id=annotator_id)

        return q.all()

    def insert(self, type, value=None, annotator_id=None):
        """
        Insert log message directly into the database, without session.
        """
        if self.execution_number is None:
            q = database.db.session.query(entity.Log)
            q = q.filter(entity.Log.execution_number != None)
            q = q.order_by(entity.Log.execution_number.desc())
            q = q.limit(1)

            last_log = q.all()

            if len(last_log) == 0:
                self.execution_number = 1
            else:
                self.execution_number = last_log[0].execution_number + 1

        dthandler = lambda obj: obj.isoformat() if isinstance(obj, datetime.datetime) else None
        value_encoded = json.dumps(value, default=dthandler, indent=1)

        database.db.engine.execute(
            entity.Log.__table__.insert(),
            [{'type': unicode(type), 'value': unicode(value_encoded), 'created_by_id': annotator_id, 'execution_number': self.execution_number}]
        )

annotators = Annotators()
videos = Videos()
annotation_objects = AnnotationObjects()
annotation_attributes = AnnotationAttributes()
annotation_values = AnnotationValues()
logs = Logs()

logger.debug('Repository object instances created.')
