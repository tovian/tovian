# -*- coding: utf-8 -*-

"""
Buffer module:
- class Buffer caches data loaded from database.
"""

import logging
import sys
from PySide.QtCore import QObject, Signal, Slot, QMutex
from tovian import models


logger = logging.getLogger(__name__)
logger.debug('Import ' + __name__)


class Buffer(QObject):
    """
    Class buffers annotation objects to cache from database for given frame or frame interval.
    :param video: reference to video object
    :type video: tovian.models.entity.Video
    :param parent: parent widget
    :type parent: PySide.QtCore.QObject
    """

    checkBufferState = Signal()
    buffering = Signal()
    buffered = Signal()
    initialized = Signal()

    MAX_MEMORY_USAGE = 52428800     # 50MB

    def __init__(self, video, user_id, parent=None):
        super(Buffer, self).__init__(parent)
        self.mutex = QMutex()
        self.video = video
        self.last_frame_accessed = (0, 0)
        self.displayed_frames_range = 1     # must be odd
        self.video_frame_count = self.video.frame_count
        self.video_frame_fps = self.video.fps
        self.user_id = user_id

        self.cache = {}
        self.cached_min_frame = 0
        self.cached_max_frame = 0
        self.cached_time = 10               # seconds
        self.cached_time_border = 0.25      # 25 percent from cached interval, where it starts to buffer new objects

        self.checkBufferState.connect(self.__checkBuffer)

    def initBuffer(self):
        """
        Called just first time after initializing buffed and moving to separated thread.
        """
        new_start = 0
        new_stop = int(self.cached_time * self.video_frame_fps)
        new_stop = new_stop if new_stop < self.video_frame_count else self.video_frame_count

        logger.debug("Filling buffer on interval [%s, %s]", new_start, new_stop)
        self.__bufferObjects(new_start, new_stop)
        self.initialized.emit()

    def setDisplayedFrameRange(self, length):
        """
        Sets how long frame interval is displayed (non-vis annotations).
        i.e. 11 meas [currentframe-5, currentframe+5]
        :param length: range length
        :type length: int
        """
        logger.debug("Setting new displayed range value %s", length)
        self.mutex.lock()
        self.displayed_frames_range = length
        self.mutex.unlock()

    def getObjectsInFrame(self, frame):
        """
        Returns list of annotation objects for given frame. When accessing to cache, cached is locked for other access.
        :type frame: int
        :rtype: tuple of (tovian.models.entity.AnnotationObject, int, int)
        :raise AttributeError: if given frame number is out of range [0, video.frame_count]
        """
        logger.debug("Called get an_object from buffer for frame: %s", frame)

        if frame < 0 or frame > self.video_frame_count:
            raise AttributeError("Given frame number %s is out of range [0, %s]" % (frame, self.video_frame_count))

        # --- locked ----
        self.mutex.lock()
        try:
            objects = self.cache[frame]
        except KeyError:
            logger.error("Buffer objects could not be found for frame: %s", frame)
            models.repository.logs.insert('gui.exception.get_obj_from_buffer_error',
                                          "Buffer objects could not be found for frame: %s" % frame,
                                          annotator_id=self.user_id)
            objects = self.video.annotation_objects_in_frame(frame)
        else:
            objects = objects.values()

        finally:
            self.last_frame_accessed = (frame, frame)
            self.mutex.unlock()                 # don't forget to release lock
        # ---------------

        self.checkBufferState.emit()
        return tuple(objects)

    def getObjectsInFrameInterval(self, frame_from, frame_to):
        """
        Returns list of annotation objects for given frame interval.
        :type frame_from: int
        :type frame_to: int
        :rtype: tuple of (tovian.models.entity.AnnotationObject, int, int)
        :raise AttributeError: if given frame number interval is not in range [0, video.frame_count] or is invalid
        """
        logger.debug("Called get an_object from buffer for frame interval [%s, %s]", frame_from, frame_to)

        if frame_from > frame_to:
            raise AttributeError("frame_from '%s' is greater than frame_to '%s'" % (frame_from, frame_to))

        if frame_from < 0 or frame_to < 0 or frame_to > self.video_frame_count or frame_from > self.video_frame_count:
            raise AttributeError("Given frame interval [%s, %s] is out of range [0, %s]"
                                 % (frame_from, frame_to, self.video_frame_count))

        if frame_from == frame_to:
            objects = self.getObjectsInFrame(frame_from)
            return objects

        objects = []
        self.mutex.lock()
        try:
            for frame in range(frame_from, frame_to + 1):
                try:
                    data = self.cache[frame]
                except KeyError:
                    logger.error("Buffer objects could not be found for frame: %s", frame)
                    models.repository.logs.insert('gui.exception.get_obj_from_buffer_error',
                                                  "Buffer objects could not be found for frame: %s" % frame,
                                                  annotator_id=self.user_id)
                    data = self.video.annotation_objects_in_frame(frame)
                else:
                    data = data.values()

                objects.extend(data)       # converts iterator to values
        finally:
            self.last_frame_accessed = (frame_from, frame_from)
            self.mutex.unlock()

        self.checkBufferState.emit()
        return tuple(set(objects))

    def resetBuffer(self, frame, clear_all=False, clear_object=None):
        """
        Reset buffer - loads new objects depending on given frame number (i.e. when seeking to new frame).
        Method requests lock when clearing cache!
        :param frame: target frame
        :type frame: int
        :param clear_all: manually clears buffer
        :type clear_all: bool
        :param clear_object:  object that has to be refreshed in buffer (object_id, old_start_frame, old_end_frame)
        :raise ValueError: if given frame number is out of range [0, video.frame_count] |
        when new min and max cached frame are equaled or invalid
        """
        #logger.debug("Locking thread")
        #self.mutex.lock()
        #self.last_frame_accessed = (min_frame_interval, max_frame_interval)
        #self.mutex.unlock()
        #logger.debug("Thread unlocked")

        if frame < 0 or frame > self.video_frame_count:
            raise ValueError("Given frame number %s is out of range [0, %s]" % (frame, self.video_frame_count))

        if not clear_all and not clear_object:
            # if new frame has been already cached
            if frame in self.cache:
                min_frame = frame - ((self.displayed_frames_range - 1) / 2.0)
                max_frame = frame + ((self.displayed_frames_range - 1) / 2.0)

                min_frame = 0 if min_frame < 0 else min_frame
                max_frame = self.video_frame_count if max_frame > self.video_frame_count else max_frame

                # if new frame display frame range is also cached
                if self.cached_min_frame <= min_frame and self.cached_max_frame >= max_frame:
                    logger.debug("New frame and displayed frame interval is cached and no need to reset")
                    return
                else:
                    logger.debug("Target frame is cached, but displayed frame range isn't.")
            else:
                logger.debug("Target frame is not cached.")
        # calculate new start_frame and stop_frame
        new_start_frame = frame - int((self.cached_time / 2.0) * self.video_frame_fps)
        new_stop_frame = frame + int((self.cached_time / 2.0) * self.video_frame_fps)
        new_start_frame = 0 if new_start_frame < 0 else new_start_frame
        new_stop_frame = self.video_frame_count if new_stop_frame > self.video_frame_count else new_stop_frame

        if new_stop_frame == new_start_frame or new_stop_frame < new_start_frame:
            logger.error("New start_frame '%s' and stop_frame '%s' are equal or invalid.",
                         new_start_frame, new_stop_frame)
            raise ValueError("New start_frame '%s' and stop_frame '%s' are equal or invalid."
                             % (new_start_frame, new_stop_frame))

        if clear_object:
            object_id, old_start, old_end = clear_object

            logger.debug("Deleting old object data from cache")
            self.mutex.lock()
            for i in range(old_start, old_end + 1):
                cache_data = self.cache[i]
                del cache_data[object_id]
            self.mutex.unlock()
            logger.debug("Thread unlocked")

            ## TODO DELETE !!!!!!!!!!!!!!!!!!!!!!!! FOR DEBUGGING PURPOSES
            #for key, value in self.cache.iteritems():
            #    if object_id in value:
            #        print key, value
            #        raise Exception()

            logger.debug("Clearing object id '%s' from buffer and resetting for new frame: %s", object_id, frame)
            self.__bufferObjectByID(frame, object_id)

        else:
            logger.debug("Resetting and clearing whole buffer for new frame: %s", frame)

            self.mutex.lock()
            self.cache = {}
            self.mutex.unlock()
            self.__bufferObjects(new_start_frame, new_stop_frame)       # manually invoked buffering

    def __bufferObjects(self, frame_from, frame_to):
        """
        Called to buffer new objects from database for given frame interval.
        Method requests lock when writing to cache!
        :type frame_from: int
        :type frame_to: int
        :raise ValueError: When frame_from or frame_to has invalid value (out of range, etc.)
        """
        logger.debug("Tries buffer new frame interval [%s, %s]...", frame_from, frame_to)
        if frame_from > frame_to or frame_from < 0 or frame_to > self.video_frame_count:
            raise ValueError("Invalid frame_from '%s' and frame_to values '%s'", frame_from, frame_to)

        self.mutex.lock()
        try:
            objectsTuples = self.video.annotation_objects_in_frame_intervals([(frame_from, frame_to)])
        except Exception:
            # TODO display error to user
            logger.exception("Error when buffering new objects from database on interval [%s, %s]", frame_from, frame_to)
            models.repository.logs.insert('gui.exception.buffering_new_obj_error',
                                          "Error when buffering new objects from database on interval [%s, %s]" %
                                          (frame_from, frame_to),
                                          annotator_id=self.user_id)
            self.mutex.unlock()         # don't forget to release lock
            return

        cleared = not self.cache
        self.buffering.emit()

        #logger.debug("Locking thread -> adding new data to cache")
        #self.mutex.lock()               # request lock
        try:
            for frame in range(frame_from, frame_to + 1):
                try:
                    frame_dict = self.cache[frame]
                except KeyError:
                    self.cache[frame] = {}
                    frame_dict = self.cache[frame]

                # add record to cache
                for objectTuple in objectsTuples:
                    an_object, start_frame, end_frame = objectTuple
                    if start_frame <= frame <= end_frame:
                        frame_dict[an_object.id] = objectTuple

            # if cache has been cleared when method called, set min and max pointers as usually
            if cleared:
                self.cached_max_frame = frame_to
                self.cached_min_frame = frame_from

            # if don't, cache has been extended, so moves pointer a bit
            else:
                if frame_from < self.cached_min_frame:
                    self.cached_min_frame = frame_from
                if frame_to > self.cached_max_frame:
                    self.cached_max_frame = frame_to

        finally:
            self.mutex.unlock()         # don't forget to release lock

        self.buffered.emit()
        logger.debug("Buffered new time interval [%s, %s]", frame_from, frame_to)

    def __bufferObjectByID(self, target_frame, object_id):
        """
        Buffer new object by given ID from database on given frame
        :type target_frame: int
        :type object_id: int
        :raise ValueError: When frame is out of range
        """
        logger.debug("Trying to buffer new object id '%s' on frame '%s'", object_id, target_frame)
        if target_frame < 0 or target_frame > self.video_frame_count:
            raise ValueError("Given frame number is out of video frame count range")

        try:
            objectTuples = self.video.annotation_objects_in_frame_intervals([(target_frame, target_frame)],
                                                                            [object_id, ])
        except Exception:
            # TODO display error to user
            logger.exception("Error when buffering new object id '%s' from database on on frame '%s'",
                             object_id, target_frame)
            models.repository.logs.insert('gui.exception.buffering_new_obj_error',
                                          "Error when buffering new object id '%s' from database on on frame '%s'" %
                                          (object_id, target_frame),
                                          annotator_id=self.user_id)
            return

        if not objectTuples:
            logger.warning("No object id '%s' for frame '%s' in database!")
            return
        elif len(objectTuples) > 1:
            logger.warning("Returned more than one object by id from database!")

        self.buffering.emit()

        logger.debug("Locking thread -> adding to cache new data")
        self.mutex.lock()
        try:
            an_object, start_frame, end_frame = objectTuples[0]

            for frame in range(start_frame, end_frame + 1):
                try:
                    frame_dict = self.cache[frame]
                except KeyError:
                    self.cache[frame] = {}
                    frame_dict = self.cache[frame]

                frame_dict[an_object.id] = objectTuples[0]

        finally:
            self.mutex.unlock()
            logger.debug("Thread unlocked")

        self.buffered.emit()
        logger.debug("Buffered new by id '%s' on frame '%s'", object_id, target_frame)

    @Slot()
    def __checkBuffer(self):
        """
        Method called when some data in cache has been accessed to check,
        if needs to be loaded new objects from database.
        """
        memory_usage = sys.getsizeof(self.cache)

        if memory_usage > self.MAX_MEMORY_USAGE:
            logger.warning("Reached maximum allowed memory usage '%s' bytes -> resetting buffer", self.MAX_MEMORY_USAGE)
            lower_accessed_frame, higher_accessed_frame = self.last_frame_accessed
            if lower_accessed_frame == higher_accessed_frame:
                frame = higher_accessed_frame
            else:
                frame = ((higher_accessed_frame - lower_accessed_frame) / 2) + lower_accessed_frame

            self.resetBuffer(frame, clear_all=True)
            return

        cached_min_border = self.cached_min_frame - self.last_frame_accessed[0]
        cached_max_border = self.cached_max_frame - self.last_frame_accessed[1]
        allowed_border = self.cached_time_border * self.cached_time * self.video_frame_fps

        # ----
        # If the last_accessed_frame pointer is between borders (typically between 25% and 75% cache), do nothing.
        # else cache new interval and merge cached data
        # i.e. cache status  =   |bottom|--------------0current0--|top|   => max border passed, cache new objects =>
        #      => new status =   |bottom|--------------0current0--(-----------------------------)|top|
        # ----

        # bottom border
        if cached_min_border > -allowed_border:
            new_stop = self.cached_min_frame - 1
            new_start = new_stop - int(self.cached_time * self.video_frame_fps)

            new_start = 0 if new_start < 0 else new_start
            new_start = self.video_frame_count if new_start > self.video_frame_count else new_start
            new_stop = 0 if new_stop < 0 else new_stop
            new_stop = self.video_frame_count if new_stop > self.video_frame_count else new_stop

            if new_start != new_stop:
                logger.debug("Check buffer - buffer needs to load new objects, direction down")

                self.__bufferObjects(new_start, new_stop)

        # upper border
        elif cached_max_border < allowed_border:
            new_start = self.cached_max_frame + 1
            new_stop = new_start + int(self.cached_time * self.video_frame_fps)

            new_start = 0 if new_start < 0 else new_start
            new_start = self.video_frame_count if new_start > self.video_frame_count else new_start
            new_stop = 0 if new_stop < 0 else new_stop
            new_stop = self.video_frame_count if new_stop > self.video_frame_count else new_stop

            if new_start != new_stop:
                logger.debug("Check buffer - buffer needs to load new objects, direction up")

                self.__bufferObjects(new_start, new_stop)

        else:
            logger.debug("Check buffer - status OK")

    @staticmethod
    def bufferFinished():
        """
        Called when buffer thread is finished (closed).
        """
        logger.debug("Buffer thread closed.")

    @staticmethod
    def bufferTerminated():
        """
        Called when buffer thread is terminated (forced to close).
        """
        logger.warning("Buffer thread terminated!")