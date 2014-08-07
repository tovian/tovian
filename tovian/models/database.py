# -*- coding: utf-8 -*-

"""
    Module that keeps global references to database engine and session.
"""

import sqlalchemy
from sqlalchemy.orm import sessionmaker
from sqlalchemy import event
import logging
import re
import datetime
import time
import entity
import warnings
import threading

import defaults


logger = logging.getLogger(__name__)
logger.debug('Import ' + __name__)


class Database():
    engine = None
    session = None
    opened_url = None
    cursor_execute_locked_by_thread = None # to detect parallel calls

    profiler = {'sql_count': 0L, 'last_access': None, 'before_cursor_execute_time': 0}

    def open(self, database_url, echo=False):
        if self.opened_url == database_url:
            # do not open already opened connection to the same url
            return

        self.engine = sqlalchemy.create_engine(database_url, echo=echo)

        # register event handler
        event.listen(self.engine, "before_cursor_execute", self._before_cursor_execute)
        event.listen(self.engine, "after_cursor_execute", self._after_cursor_execute)

        self.open_session()

        self.opened_url = database_url

    def close(self):
        logger.debug("Closing database connection")

        self.close_session()

        if self.engine is not None:
            self.engine.dispose()
            self.engine = None

        self.opened_url = None

    def open_session(self):
        self.close_session()

        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        logger.debug("Session was created")

    def close_session(self):
        if self.session:
            self.session.close()

        logger.debug("Session was closed")

    def open_from_config(self, config, environment):
        self.open(config.get(environment, 'database.url'), config.getboolean(environment, 'sqlalchemy.engine.echo'))

        self.opened_environment = environment

        url = config.get(environment, 'database.url')
        url = re.sub("\:[^/](.*)\@", ":...@", url) # hide password
        logger.debug("Database was opened: %s (%s environment)" % (url, environment))

        if not config.getboolean(environment, 'sqlalchemy.engine.echo'):
            # disable SQL alchemy warnings
            warnings.filterwarnings('ignore', '^Object of type .* not in session, add operation along .* will not proceed$', sqlalchemy.exc.SAWarning)


    def recreate_tables(self):
        """
        Drops all tables, creates them again.
        """
        import entity

        # reopen new session (removes pending entity intances)
        self.open_session()

        entity.Base.metadata.drop_all(bind=self.engine)
        entity.Base.metadata.create_all(self.engine)

        logger.debug("Tables were recreated.")

    def insert_default_data(self):
        """
        Insert default data into empty database
        """
        entities = defaults.create_defaults()
        self.session.add_all(entities)

        # increase autoincrement to 999, keep IDs under 1000 for future usage
        attribute_foo = entity.AnnotationAttribute(id=999, name=u'foo', data_type=u'unicode',
                                                   annotation_object_type=u'rectangle', is_global=False)

        self.session.add(attribute_foo)
        self.session.commit()

        self.session.delete(attribute_foo)
        self.session.commit()

        logger.debug("Default data inserted to database.")


    def _before_cursor_execute(self, conn, cursor, statement, parameters, context, executemany):
        current_thread_name = threading.current_thread().name

        if self.cursor_execute_locked_by_thread is not None and self.cursor_execute_locked_by_thread != current_thread_name:
            raise Exception('Parallel call to database detected! (%s, %s) / (%s, %s)' % (statement, parameters, self.cursor_execute_locked_by_thread, current_thread_name))

        self.cursor_execute_locked_by_thread = current_thread_name

        self.profiler['before_cursor_execute_time'] = time.time()

        # count executed sql statements
        self.profiler['sql_count'] += 1
        self.profiler['last_access'] = datetime.datetime.now()

    def _after_cursor_execute(self, conn, cursor, statement, parameters, context, executemany):
        self.cursor_execute_locked_by_thread = None

        duration_ms = 1000 * (time.time() - self.profiler['before_cursor_execute_time'])

        #logger.debug('SQL execution duration: %4.2f ms' % (duration_ms))

        if duration_ms > 300:
            logger.warning('Slow SQL (%4.2f ms): %s %s' % (duration_ms, statement, parameters))


db = Database()

logger.debug('Database object instance created.')
