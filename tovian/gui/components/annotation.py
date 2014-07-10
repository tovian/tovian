# -*- coding: utf-8 -*-

"""
Annotation class handles user video annotation actions:
 - downloading and displaying data from database
 - initializing data buffer
 - processing and committing changes
"""

__version__ = "$Id: annotation.py 356 2014-05-06 18:39:59Z herbig $"

import time
import ast
import logging

from PySide.QtGui import *
from PySide.QtCore import *

from tovian.gui.dialogs.attribselect import AttribSelectionDialog
from tovian import models
from tovian.models import repository
from tovian.gui.dialogs.mask import MaskDialog
import graphics


logger = logging.getLogger(__name__)
logger.debug('Import ' + __name__)


class Annotation(QObject):
    """
    Class handles displaying and drawing new annotations.
    :type parent: tovian.gui.dialogs.mainwindow.MainApp
    """

    error_title = u"Error occurred"
    loading_an_objects_error = u"Exception when loading annotation objects:<br />%s"
    loading_global_values_error = u"Error when loading global annotation values:<br />%s"
    loading_local_values_error = u"Error when loading local annotation values:<br />%s"
    syntax_error_msg = u"Error! Edited values '%s' has wrong syntax for data type '%s'"
    committing_msg = u"Saving changes to database..."
    committing_successfully_msg = u"Changes saved successfully to database"
    committing_failed_msg = u"Saving to database failed, check the log file"
    reverting_msg = u"Reverting changes since last save..."
    reverting_successfully_msg = u"Changes reverted successfully since last save"
    reverting_failed_msg = u"Reverting changes failed, check the log file"
    deleting_object_msg = u"Deleting selected object..."
    deleting_object_msg_successfully = u"Object has been deleted successfully"
    deleting_object_msg_failed = u"Deleting the selected object failed"
    deleting_attrib_msg = u"Deleting selected attribute..."
    deleting_attrib_msg_successfully = u"Selected attribute has been deleted successfully"
    deleting_attrib_msg_failed = u"Deleting the selected attribute failed"
    add_new_attrib_select_msg = u"Select new attribute..."
    add_new_attrib_writing_msg = u"New attribute selected, writing changes..."
    add_new_attrib_successfully_msg = u"Successfully added new attribute"
    add_new_attrib_failed_msg = u"Adding new attribute failed, check the log file"
    extending_nonvis_annotation_msg = u"Extending current non-visual annotation..."
    extending_nonvis_annotation_successfully_msg = u"Non-visual annotation extended successfully"
    extending_nonvis_annotation_failed_msg = u"Failed to extend non-visual annotation!"
    add_new_local_attrib_btn_text = u"Add new local attribute"
    add_new_global_attrib_btn_text = u"Add new global attribute"
    adding_new_object_msg = u"Adding new object to database..."
    adding_new_object_successfully_msg = u"New object has been added successfully"
    adding_new_object_failed_msg = u"Adding new object failed, check the log file"
    adding_new_nonvis_object_msg = u"Adding new non-visual object to database..."
    adding_new_nonvis_object_successfully_msg = u"New non-visual object has been added successfully"
    adding_new_nonvis_object_failed_msg = u"Adding new non-visual object failed, check the log file"
    changes_processed_msg = u"Changes processed successfully"
    geometry_changes_processed_msg = u"Geometry changes processed successfully"
    selected_object_msg = u"Selected object type '%s' id: %s"
    no_next_annotation_msg = u"There is no next annotation to jump"
    no_prev_annotation_msg = u"There is no previous annotation to jump"

    action_edit_on_msg = u"Edit object"
    action_edit_off_msg = u"Leave edit mode"
    edited_status_msg = u"Edit mode is enabled. Edited object id: %s"

    description_attrib_text = u"Description"
    type_attrib_text = u"Type"
    begin_attrib_text = u"Begin frame"
    end_attrib_text = u"End frame"
    created_by_attrib_text = u"Created by"
    modified_by_attrib_text = u"Modified by"
    object_id_text = u"ID"

    # init
    VIS_OBJ_POS_ATTRIBS = (u'position_rectangle', u'position_circle', u'position_point', u'position_ellipse')
    NON_VIS_TYPE = u'nonvisual'
    NON_VIS_POS_ATTRIB = u'position_nonvisual'
    WAIT_TIMEOUT = 1                    # time in sec

    error = Signal()

    def __init__(self, parent):
        super(Annotation, self).__init__(parent)
        # parent references
        self.user = parent.user
        self.video = parent.video
        self.scene = parent.scene
        self.player = parent.player
        self.globalTable = parent.globalTable
        self.localTable = parent.localTable
        self.annotationsTable = parent.annotationsTable
        self.nonVisTable = parent.nonVisTable
        self.fpsLabel = parent.fpsLabel
        self.statusbar = parent.statusbar
        self.MSG_DURATION = parent.MSG_DURATION
        self.SHORT_MSG_DURATION = parent.SHORT_MSG_DURATION
        self.buffer = parent.buffer
        self.toolsAndVideoTabWidget = parent.toolsAndVideoTabWidget
        self.nonvis_annotation_enabled = parent.nonvis_annotation_enabled
        self.label_font_size = parent.SMALL_FONT

        # var init
        self.video_total_time = self.player.totalTime()
        self.scene_items = []
        self.frame_cache = {}
        self.un_committed_changes = False
        self.committing = False
        self.processing_changes = False
        self.processing_objects = False
        self.closing = False
        self.position_attrib_in_table_index = None
        self.position_an_value = None
        self.displayed_object_id = None
        self.local_attribs_in_table = []
        self.global_attribs_in_table = []
        self.remaining_local_attribs = []
        self.remaining_global_attribs = []
        self.selected_object_tuple = None
        self.edited_manual_pos_set = False
        self.edited_graphics_object = None
        self.edited_id = None
        self.edited_is_visual = None
        self.selected_graphics_object = None
        self.video_attributes = self.video.annotation_attributes
        self.completers = {}
        self.initCompleters()

        self.nonvis_table_records = []
        self.nonvis_objects_in_frame_range = {}
        self.annotation_table_is_visible = True if self.toolsAndVideoTabWidget.currentIndex() == 1 else False
        self.video_frame_count = self.video.frame_count

        self.default_colors = self.video.get_option('gui.color')

        if self.nonvis_annotation_enabled:
            self.nonvis_column_count = 21
            self.buffer.setDisplayedFrameRange(self.nonvis_column_count)
            self.nonVisTable.setColumnCount(self.nonvis_column_count)
            header = self.nonVisTable.horizontalHeader()
            middle_column = (self.nonvis_column_count - 1) / 2
            header.setResizeMode(middle_column, QHeaderView.Stretch)
        else:
            self.nonvis_column_count = 1

        logger.debug("Annotation class initialized")

    @Slot(int, int)
    def processObjects(self, current_time=None, current_frame=None, draw=True):
        """
        Called every frame to process annotation objects.
        Method draws annotation objects and fills attribute table for selected object.
        :type current_frame: int
        :type current_time: int
        :param draw: tells to skip drawing
        :type draw: bool
        """
        # to prevent collision when committing or processing new changes
        if self.committing or self.processing_changes or self.closing or self.player.isStopped:
            if current_frame is not None:
                self.fpsLabel.setText("Frame #%s" % current_frame)
            logger.debug("Unable process objects, waiting until finishes commit/process changes/closing/video_init")
            return

        # t01 = time.time() * 1000L

        current_frame = self.player.getCurrentFrame() if current_frame is None else current_frame
        self.fpsLabel.setText("Frame #%s" % current_frame)                       # display current frame in status bar

        # ----------------------------------------------------------------------------------------
        logger.debug("Called processObjects, frame: %s", current_frame)
        # -----------------------------------------------------------------------------------------

        self.processing_objects = True
        self.frame_cache = {}
        self.nonvis_objects_in_frame_range = {}

        # fill annotation table only if it's visible
        if self.nonvis_annotation_enabled:
            self.annotationsTable.setRowCount(0)

        # redraw scene objects if drawing is not disabled
        if draw and self.scene_items:
            self.scene.clearScene(self.scene_items)
            self.scene_items = []

        try:
            # --- GET ANNOTATION OBJECTS FROM BUFFER ---
            if self.nonvis_annotation_enabled:
                frame_from = current_frame - ((self.nonvis_column_count - 1) / 2)
                frame_to = current_frame + ((self.nonvis_column_count - 1) / 2)
                frame_from = 0 if frame_from < 0 else frame_from
                frame_to = 0 if frame_to < 0 else frame_to
                frame_from = self.video.frame_count if frame_from > self.video.frame_count else frame_from
                frame_to = self.video.frame_count if frame_to > self.video.frame_count else frame_to
                retrieved_objects = self.buffer.getObjectsInFrameInterval(frame_from, frame_to)
            else:
                retrieved_objects = self.buffer.getObjectsInFrame(current_frame)

        except Exception, e:
                logger.exception("Error when loading annotation objects in frame: %s", current_frame)
                models.repository.logs.insert('gui.exception.process_objects_loading_error',
                                              "Error when loading annotation objects in frame: %s" % current_frame,
                                              annotator_id=self.user.id)
                self.player.stop()
                self.error.emit()
                self.processing_objects = False
                # TODO emit error with error text instead of messagebox (display msg box in GUI module)
                QMessageBox(QMessageBox.Critical, self.error_title, self.loading_an_objects_error % e).exec_()
                return

        # ------------------------------------------

        # ------------ PROCESS ATTRIBUTES FROM OBJECTS --------------
        if retrieved_objects:
            # *** ITERATE OVER ANNOTATION OBJECTS ***
            i = 0
            for an_object_tuple in retrieved_objects:
                #t000 = time.time() * 1000

                if not an_object_tuple:
                    logger.error("Annotation object tuple for frame '%s' is empty or None", current_frame)
                    continue

                # --- GET AND STORE DATA IN CACHE ---
                an_object, start_frame, end_frame = an_object_tuple

                # if not active in frame, do not store to frame_cache but save non-vis annotation
                if not (start_frame <= current_frame <= end_frame):
                    if an_object.type == self.NON_VIS_TYPE:
                        self.nonvis_objects_in_frame_range[an_object.id] = an_object_tuple
                    continue

                local_attributes = self.getLocalAttributes(an_object, current_frame, draw)
                global_attributes = self.getGlobalAttributes(an_object)
                if local_attributes is None or global_attributes is None:
                    logger.error("Returned attributes for object '%s' is None", an_object)
                    continue

                #print "one po loop <%s>" % an_object, (time.time() * 1000L) - t000
                self.frame_cache[an_object.id] = (an_object_tuple, local_attributes, global_attributes)
                # --- **************************** ---

                # --- add record to annotation table ---
                if self.annotation_table_is_visible:
                    self.annotationsTable.insertRow(self.annotationsTable.rowCount())

                    object_comment = QTableWidgetItem(an_object.public_comment)
                    object_type = QTableWidgetItem(an_object.type)
                    object_id = QTableWidgetItem(str(an_object.id))
                    object_id.setTextAlignment(Qt.AlignCenter)
                    self.annotationsTable.setItem(i, 0, object_comment)
                    self.annotationsTable.setItem(i, 1, object_type)
                    self.annotationsTable.setItem(i, 2, object_id)
                # --- ****************************** ---

                # store non-visual an. objects
                if self.nonvis_annotation_enabled and an_object.type == self.NON_VIS_TYPE:
                    self.nonvis_objects_in_frame_range[an_object.id] = an_object_tuple
                i += 1

            # **********************************************

        # only is some object is selected
        if self.edited_id is not None:
            self.reloadAndMarkSelectedObject(current_frame)                          # mark selected object on scene
            self.displayAttributes(current_frame)                                    # fill the attribute table

        if self.nonvis_annotation_enabled:
            self.displayNonVisAnnotations(current_frame)

        self.processing_objects = False

        # t11 = time.time() * 1000
        # print "ProcessObjects: ", t11 - t01

    def getLocalAttributes(self, an_object, current_frame, draw):
        """
        Gets local attributes for given frame and object and draws annotation objects on the scene.
        :param draw: if an_object should be drawn
        :type an_object: tovian.models.entity.AnnotationObject
        :type current_frame: int
        :type draw: bool
        :return: list of local attributes
        :rtype: list of tovian.models.entity.AnnotationValue
        """
        try:
            local_values = an_object.annotation_values_local_interpolate_in_frame(current_frame)
        except Exception, e:
            self.player.stop()
            self.error.emit()
            logger.exception("Error when loading local annotation values from database")
            models.repository.logs.insert('gui.exception.loading_local_anvalues_error',
                                          "Error when loading local annotation values from database",
                                          annotator_id=self.user.id)
            QMessageBox(QMessageBox.Critical, self.error_title, self.loading_local_values_error % e).exec_()
            return None

        # if there is some local values
        if local_values and draw:
            # draw the object
            for value in local_values:
                # ? position attribute => draw object
                if value.annotation_attribute.name in self.VIS_OBJ_POS_ATTRIBS:
                    self.drawObject(value, current_frame)
            if self.parent().zoom > 1:
                self.scene.scaleItemsPen(self.parent().zoom)

        return local_values

    def getGlobalAttributes(self, an_object):
        """
        Obtains global attributes for given frame and object.
        :type an_object: tovian.models.entity.AnnotationObject
        :return: list of local attributes
        :rtype: list of tovian.models.entity.AnnotationValue
        """
        try:
            global_values = an_object.annotation_values_global()
        except Exception, e:
            self.player.stop()
            self.error.emit()
            logger.exception("Error when loading global annotation values from database")
            models.repository.logs.insert('gui.exception.loading_global_anvalues_error',
                                          "Error when loading global annotation values from database",
                                          annotator_id=self.user.id)
            QMessageBox(QMessageBox.Critical, self.error_title, self.loading_global_values_error % e).exec_()
        else:
            return global_values

    def drawObject(self, value, current_frame):
        """
        Draws graphics object depending on type and position.
        :type value: tovian.models.entity.AnnotationValue
        :type current_frame: int
        """
        # initializing the object
        data_type = value.annotation_attribute.data_type
        an_object = value.annotation_object

        if not self.label_font_size:
            labels = ('', '')
        else:
            labels = value.annotation_object.get_text(current_frame)

        if data_type == u'position_rectangle':
            graphics_object = self.drawRect(value, labels)
        elif data_type == u'position_circle':
            graphics_object = self.drawCircle(value, labels)
        elif data_type == u'position_point':
            graphics_object = self.drawPoint(value, labels)
        else:
            raise NotImplementedError("Given data type '%s' is not implemented yet" % data_type)

        # drawn object is in edit mode
        if an_object.id == self.edited_id and self.edited_graphics_object is not None:
            self.edited_manual_pos_set = True
            self.edited_graphics_object.COLOR = graphics_object.normal_color
            self.edited_graphics_object.HIGHLIGHTER_COLOR = graphics_object.selected_color
            self.edited_graphics_object.NOT_ACTIVE_COLOR = graphics_object.not_active_color
            self.edited_graphics_object.setPen(graphics_object.pen())
            self.edited_graphics_object.setFontSize(self.label_font_size)
            print labels[0], labels[1]
            self.edited_graphics_object.setLabels(labels[0], labels[1])
            self.edited_graphics_object.setPos(graphics_object.pos())
            self.edited_graphics_object.resize(graphics_object.width, graphics_object.height)

            if value.is_interpolated:
                self.edited_graphics_object.drawDotted()

        elif an_object.id == self.edited_id and self.edited_graphics_object is None:
            graphics_object.setData(0, an_object.id)
            self.scene.addItem(graphics_object)
            self.edited_graphics_object = graphics_object

        else:
            # match graphics an_object with real an_object (parent) and add the object to scene
            graphics_object.setData(0, an_object.id)
            if value.is_interpolated:
                graphics_object.drawDotted()
            self.scene_items.append(graphics_object)
            self.scene.addItem(graphics_object)

    def drawRect(self, value, labels):
        """
        Initializes and returns rect graphics object to depending on given position.
        :type value: tovian.models.entity.AnnotationValue
        :type labels: tuple of unicode
        :rtype : tovian.gui.Components.graphics.AnnotationRect
        """
        video_size = self.scene.getVideoSize()
        scene_width = video_size.width()
        scene_height = video_size.height()

        # get the original (not scaled) dimensions and coordinates
        x1, y1, x2, y2 = value.value[0], value.value[1], value.value[2], value.value[3]
        width_orig = x2 - x1
        height_orig = y2 - y1
        x_orig = x1 + width_orig / 2.0
        y_orig = y1 + height_orig / 2.0

        # calculate scaled dimensions and coordinates depending on current video view width/height
        x_scaled = (float(x_orig) / self.video.width) * scene_width
        y_scaled = (float(y_orig) / self.video.height) * scene_height
        width_scaled = (float(width_orig) / self.video.width) * scene_width
        height_scaled = (float(height_orig) / self.video.height) * scene_height

        return graphics.AnnotationRect(x_scaled, y_scaled, width_scaled, height_scaled, scene=self.scene,
                                       text=labels, font_size=self.label_font_size, color=self.default_colors)

    def drawCircle(self, value, labels):
        """
        Initializes and returns circle graphics object to depending on given position.
        :type value: tovian.models.entity.AnnotationValue
        :type labels: tuple of unicode
        :rtype :  tovian.gui.Components.graphics.AnnotationCircle
        """
        video_size = self.scene.getVideoSize()
        scene_width = video_size.width()
        scene_height = video_size.height()

        # get the original (not scaled) dimensions and coordinates
        x, y, r = value.value[0], value.value[1], value.value[2]

        # calculate scaled dimensions and coordinates depending on current video view width/height
        x_scaled = (float(x) / self.video.width) * scene_width
        y_scaled = (float(y) / self.video.height) * scene_height
        r_scaled = (float(r) / self.video.width) * scene_width
        #color=value.get_option(['gui', 'color'])
        return graphics.AnnotationCircle(x_scaled, y_scaled, 2 * r_scaled, scene=self.scene,
                                         text=labels, font_size=self.label_font_size, color=self.default_colors)

    def drawPoint(self, value, labels):
        """
        Initializes and returns point graphics object to depending on given position.
        :type value: tovian.models.entity.AnnotationValue
        :type labels: tuple of unicode
        :rtype : tovian.gui.Components.graphics.AnnotationPoint
        """
        video_size = self.scene.getVideoSize()
        scene_width = video_size.width()
        scene_height = video_size.height()

        # get the original (not scaled) dimensions and coordinates
        x = value.value[0]
        y = value.value[1]

        # calculate scaled dimensions and coordinates depending on current video view width/height
        x_scaled = (float(x) / self.video.width) * scene_width
        y_scaled = (float(y) / self.video.height) * scene_height

        return graphics.AnnotationPoint(x_scaled, y_scaled, scene=self.scene,
                                        text=labels, font_size=self.label_font_size, color=self.default_colors)

    def displayAttributes(self, frame=None):
        """
        Fills the attribute table
        :type frame: int
        """
        frame = self.player.getCurrentFrame() if frame is None else frame

        # some object is selected, fill attrib tables
        if self.selected_object_tuple:
            # load attributes from frame cache
            local_attrib = self.selected_object_tuple[1]
            global_attrib = self.selected_object_tuple[2]
            self.fillLocalAttributesTable(local_attrib, frame)                     # if any, then fill the table
            self.fillGlobalAttributesTable(global_attrib, frame)

        # no object is selected -> clear the attribute table
        else:
            self.localTable.setRowCount(0)
            self.globalTable.setRowCount(0)
            self.local_attribs_in_table = []
            self.global_attribs_in_table = []

    def fillLocalAttributesTable(self, local_attrib, frame):
        """
        Fills the local attributes table
        :type frame: int
        :type local_attrib: list of tovian.models.entity.AnnotationValue
        """
        # table init
        self.localTable.clearContents()
        if self.edited_is_visual is False:
            n = len(local_attrib)           # (+) 'add new' button and (-) not visible position value
        else:
            n = len(local_attrib) + 1       # + 'add new' button

        self.local_attribs_in_table = []
        if self.localTable.rowCount() != n:
            self.localTable.setRowCount(n)

        # -------------------------------------------- FILL THE TABLE -----------------------------------------------
        i = 0
        for attrib in local_attrib:
            if attrib.value is None:
                continue

            self.local_attribs_in_table.append(attrib)         # store attribute to list (for access to table data)

            # reset column span
            if self.localTable.columnSpan(i, 0) != 1:
                self.localTable.setSpan(i, 0, 1, 1)

            # --- SET NAME ITEM ----
            # store where to find position record in table and which object is currently displayed in table
            if isinstance(attrib.annotation_attribute.name, basestring):
                name = QTableWidgetItem(attrib.annotation_attribute.name)
            else:
                name = QTableWidgetItem(str(attrib.annotation_attribute.name))
            name.setFlags(name.flags() ^ Qt.ItemIsEditable)
            self.localTable.setItem(i, 0, name)

            if attrib.annotation_attribute.name in self.VIS_OBJ_POS_ATTRIBS:
                self.position_attrib_in_table_index = i
                self.position_an_value = attrib
                self.displayed_object_id = self.selected_object_tuple[0][0].id      # TODO is it necessary ??

            # not interpolated values are bold
            if not attrib.is_interpolated:
                font = name.font()
                font.setBold(True)
                name.setFont(font)
            # -----------------------

            # ---- SET COMBOBOX ----
            if attrib.annotation_attribute.allowed_values:
                allowed_items = QComboBox()
                allowed_items.addItems(attrib.annotation_attribute.allowed_values)

                try:
                    current_index = attrib.annotation_attribute.allowed_values.index(attrib.value)
                except ValueError:
                    logger.error("Annotation value '%s' could not be find in allowed values", attrib.value)
                    models.repository.logs.insert('gui.exception.allowed_anvalues_integrity_error',
                                                  "Annotation value '%s' could not be find in allowed values" % attrib.value,
                                                  annotator_id=self.user.id)
                else:
                    allowed_items.setCurrentIndex(current_index)

                allowed_items.currentIndexChanged.connect(self.processChanges)          # if user changes the value
                self.localTable.setCellWidget(i, 1, allowed_items)
            # ----------------------

            # ---- SET LINE EDIT ----
            else:
                text = attrib.value if isinstance(attrib.value, basestring) else unicode(attrib.value)
                valueEdit = QLineEdit(text)
                valueEdit.setFrame(False)

                try:
                    completer = self.completers[attrib.annotation_attribute.name]
                except KeyError:
                    pass
                else:
                    valueEdit.setCompleter(completer)

                if not attrib.is_interpolated:
                    font = name.font()
                    font.setBold(True)
                    valueEdit.setFont(font)
                valueEdit.editingFinished.connect(self.processChanges)
                self.localTable.setCellWidget(i, 1, valueEdit)
            # ----------------------

            i += 1
        # ----------------------------------------------------------------------------------------------------------

        # ----------------------------------------- ADD NEW ATTRIB BUTTON ------------------------------------------
        if self.localTable.columnSpan(i, 0) != 2:
            self.localTable.setSpan(i, 0, 1, 2)
        addLocalAttribBtn = QPushButton(QIcon(":/icons/icons/add_attrib.png"), self.add_new_local_attrib_btn_text)
        addLocalAttribBtn.setFlat(True)
        addLocalAttribBtn.setIconSize(QSize(10, 10))
        addLocalAttribBtn.setShortcut(QApplication.translate("Annotation", "Alt+L", None, QApplication.UnicodeUTF8))
        addLocalAttribBtn.clicked.connect(self.addNewLocalAttribute)
        self.localTable.setCellWidget(i, 0, addLocalAttribBtn)

        an_object, start_frame, end_frame = self.selected_object_tuple[0]
        # ENABLE or DISABLE 'add new attrib' button
        if start_frame <= frame <= end_frame:
            # GET USED ATTRIBUTES
            used_attribs = []
            self.remaining_local_attribs = []
            # get only valid used annotation attributes
            for value in self.local_attribs_in_table:
                if type(value) is models.entity.AnnotationValue:
                    used_attribs.append(value.annotation_attribute)

            # find unused attributes
            un_used_attrib = False
            # TODO generate allowed attributes just once for the object
            for attribute in self.getAllowedAttributes(is_local=True):
                # TODO use set instead
                if not (attribute in used_attribs):
                    self.remaining_local_attribs.append(attribute)
                    un_used_attrib = True

            addLocalAttribBtn.setEnabled(un_used_attrib)
            self.parent().addLocalAttribAction.setEnabled(un_used_attrib)
        else:
            addLocalAttribBtn.setEnabled(False)
            self.parent().addLocalAttribAction.setEnabled(False)
        # -----------------------------------------------------------------------------------------------------------

    def fillGlobalAttributesTable(self, global_attrib, frame):
        """
        Fills the global attributes table
        :type frame: int
        :type global_attrib: list of tovian.models.entity.AnnotationValue
        """
        i = 4       # 4 record (item in table) before global attribs are displayed
        n = len(global_attrib)
        an_object, start_frame, end_frame = self.selected_object_tuple[0]
        self.globalTable.clearContents()
        self.globalTable.clearSpans()
        if self.globalTable.rowCount() != (n + i + 4):
            self.globalTable.setRowCount(n + i + 4)
        self.global_attribs_in_table = []

        # -------------------------------------------- FILL THE TABLE -----------------------------------------------
        # PUBLIC COMMENT
        item = QTableWidgetItem(self.description_attrib_text)
        item.setFlags(item.flags() ^ Qt.ItemIsEditable)
        self.globalTable.setItem(0, 0, item)
        # self.globalTable.setItem(0, 1, QTableWidgetItem(an_object.public_comment))
        valueEdit = QLineEdit(an_object.public_comment)
        valueEdit.setFrame(False)
        valueEdit.editingFinished.connect(self.processChanges)
        self.globalTable.setCellWidget(0, 1, valueEdit)
        # OBJECT TYPE
        item = QTableWidgetItem(self.type_attrib_text)
        item.setFlags(item.flags() ^ Qt.ItemIsEditable)
        self.globalTable.setItem(1, 0, item)
        obj_type_item = QTableWidgetItem(an_object.type)
        obj_type_item.setFlags(obj_type_item.flags() ^ Qt.ItemIsEnabled)
        self.globalTable.setItem(1, 1, obj_type_item)
        # START frame
        item = QTableWidgetItem(self.begin_attrib_text)
        item.setFlags(item.flags() ^ Qt.ItemIsEditable)
        self.globalTable.setItem(2, 0, item)
        start_frame_item = QTableWidgetItem(str(start_frame))
        start_frame_item.setFlags(start_frame_item.flags() ^ Qt.ItemIsEnabled)
        self.globalTable.setItem(2, 1, start_frame_item)
        # STOP frame
        item = QTableWidgetItem(self.end_attrib_text)
        item.setFlags(item.flags() ^ Qt.ItemIsEditable)
        self.globalTable.setItem(3, 0, item)
        stop_frame_item = QTableWidgetItem(str(end_frame))
        stop_frame_item.setFlags(stop_frame_item.flags() ^ Qt.ItemIsEnabled)
        self.globalTable.setItem(3, 1, stop_frame_item)

        # store items in table to list - for easy later access
        self.global_attribs_in_table.extend([an_object.public_comment, an_object.type, start_frame, end_frame])

        # GLOBAL ATTRIBUTES
        for attrib in global_attrib:
            self.global_attribs_in_table.append(attrib)

            # SET NAME ITEM
            if isinstance(attrib.annotation_attribute.name, basestring):
                name = QTableWidgetItem(attrib.annotation_attribute.name)
            else:
                name = QTableWidgetItem(str(attrib.annotation_attribute.name))
            name.setFlags(name.flags() ^ Qt.ItemIsEditable)
            self.globalTable.setItem(i, 0, name)

            # SET WIDGET ITEM (combobox) -  if allowed values are specified
            if attrib.annotation_attribute.allowed_values:
                allowed_items = QComboBox()
                allowed_items.addItems(attrib.annotation_attribute.allowed_values)
                try:
                    # if the value is located in allowed_values list, find its index
                    current_index = attrib.annotation_attribute.allowed_values.index(attrib.value)
                except ValueError:
                    logger.error("Annotation value '%s' could not be find in allowed values", attrib.value)
                    models.repository.logs.insert('gui.exception.allowed_anvalues_integrity_error',
                                                  "Annotation value '%s' could not be find in allowed values" % attrib.value,
                                                  annotator_id=self.user.id)
                else:
                    allowed_items.setCurrentIndex(current_index)

                allowed_items.currentIndexChanged.connect(self.processChanges)          # if user change the value
                self.globalTable.setCellWidget(i, 1, allowed_items)

            # ---- SET LINE EDIT ----
            else:
                text = attrib.value if isinstance(attrib.value, basestring) else unicode(attrib.value)
                valueEdit = QLineEdit(text)
                valueEdit.setFrame(False)

                try:
                    completer = self.completers[attrib.annotation_attribute.name]
                except KeyError:
                    pass
                else:
                    valueEdit.setCompleter(completer)

                valueEdit.editingFinished.connect(self.processChanges)
                self.globalTable.setCellWidget(i, 1, valueEdit)
            # ----------------------

            i += 1

        # CREATED BY
        item = QTableWidgetItem(self.created_by_attrib_text)
        item.setFlags(item.flags() ^ Qt.ItemIsEditable)
        self.globalTable.setItem(i, 0, item)
        created_by_name = u"" if an_object.created_by is None else an_object.created_by.name
        created_by = QTableWidgetItem(created_by_name)
        created_by.setFlags(created_by.flags() ^ Qt.ItemIsEnabled)
        self.globalTable.setItem(i, 1, created_by)
        # MODIFIED BY
        item = QTableWidgetItem(self.modified_by_attrib_text)
        item.setFlags(item.flags() ^ Qt.ItemIsEditable)
        self.globalTable.setItem(i + 1, 0, item)
        modified_by_name = u"" if an_object.modified_by is None else an_object.modified_by.name
        modified_by = QTableWidgetItem(modified_by_name)
        modified_by.setFlags(modified_by.flags() ^ Qt.ItemIsEnabled)
        self.globalTable.setItem(i + 1, 1, modified_by)
        # OBJECT ID
        item = QTableWidgetItem(self.object_id_text)
        item.setFlags(item.flags() ^ Qt.ItemIsEditable)
        self.globalTable.setItem(i + 2, 0, item)
        object_id = QTableWidgetItem(str(an_object.id))
        object_id.setFlags(object_id.flags() ^ Qt.ItemIsEnabled)
        self.globalTable.setItem(i + 2, 1, object_id)

        # store item in table to list - for easy later access
        self.global_attribs_in_table.extend([created_by_name, modified_by_name, object_id])
        # ------------------------------------------------------------------------------------------------------------

        # ---------------------------------------------  ADD NEW ATTRIB BUTTON ---------------------------------------
        if self.globalTable.columnSpan(i + 3, 0) != 2:
            self.globalTable.setSpan(i + 3, 0, 1, 2)
        addGlobalAttribBtn = QPushButton(QIcon(":/icons/icons/add_attrib.png"), self.add_new_global_attrib_btn_text)
        addGlobalAttribBtn.setFlat(True)
        addGlobalAttribBtn.setIconSize(QSize(10, 10))
        addGlobalAttribBtn.setShortcut(QApplication.translate("Annotation", "Alt+G", None, QApplication.UnicodeUTF8))
        addGlobalAttribBtn.clicked.connect(self.addNewGlobalAttribute)
        self.globalTable.setCellWidget(i + 3, 0, addGlobalAttribBtn)

        # if active in frame, enable or disable 'add new attrib' button
        if start_frame <= frame <= end_frame:
            # GET USED ATTRIBUTES
            used_attribs = []
            self.remaining_global_attribs = []
            # get only valid used annotation attributes
            for value in self.global_attribs_in_table:
                if type(value) is models.entity.AnnotationValue:
                    used_attribs.append(value.annotation_attribute)

            # find unused attributes
            un_used_attrib = False
            # TODO generate allowed attributes just once for the object
            for attribute in self.getAllowedAttributes(is_local=False):
                # TODO use set comparison instead
                if not (attribute in used_attribs):
                    self.remaining_global_attribs.append(attribute)
                    un_used_attrib = True

            addGlobalAttribBtn.setEnabled(un_used_attrib)
            self.parent().addLocalAttribAction.setEnabled(un_used_attrib)
        else:
            addGlobalAttribBtn.setEnabled(False)
            self.parent().addLocalAttribAction.setEnabled(False)
        # -----------------------------------------------------------------------------------------------------------

    def displayNonVisAnnotations(self, current_frame=None):
        """
        Displays nonVisual objects (annotations) in table
        :param current_frame: current frame
        :type current_frame: int
        """
        if not self.nonvis_annotation_enabled:
            return

        current_frame = self.player.getCurrentFrame() if current_frame is None else current_frame
        logger.debug("Called displayNonVisAnnotations in frame: %s", current_frame)

        #t0 = time.time() * 1000

        # ------ GENERATE HEADER LABELS -----------
        header = self.nonVisTable.horizontalHeader()
        header_count = header.count()
        # recalculate min/max frames and reset labels
        middle_column = (self.nonvis_column_count - 1) / 2                # middle column index
        min_frame = current_frame - middle_column
        max_frame = current_frame + middle_column
        old_section_size = header.defaultSectionSize()

        # set new header labels
        labels = [str(frame) if 0 <= frame <= self.video.frame_count else "" for frame in range(min_frame, max_frame + 1)]
        self.nonVisTable.setHorizontalHeaderLabels(labels)

        # calculates ideal section size
        first_item_size_hint = header.sectionSizeHint(0)
        last_item_size_hint = header.sectionSizeHint(header_count - 1)
        ideal_item_size_hint = max(first_item_size_hint, last_item_size_hint)
        if ideal_item_size_hint != old_section_size:
            header.setDefaultSectionSize(ideal_item_size_hint)

        # *** calculates free space for new columns and number of items which fits in ***
        free_space = self.nonVisTable.width() - (header_count * ideal_item_size_hint) - 2       # -2 ... border px
        new_items_count = int(free_space / ideal_item_size_hint) - 2         # -2 .. middle item needs to be the widest

        # column count must be odd
        if (self.nonvis_column_count + new_items_count) % 2 == 0:
            new_items_count -= 1

        # if some new items could be fit on -> recalculate ranges and labels
        if new_items_count != 0:
            # save new column_count value and reset the value in buffer
            self.nonvis_column_count += new_items_count
            self.nonvis_column_count = self.nonvis_column_count if self.nonvis_column_count >= 1 else 1
            self.buffer.setDisplayedFrameRange(self.nonvis_column_count)

            # recalculate again min/max frames and reset labels
            header.setResizeMode(middle_column, QHeaderView.Fixed)
            header.resizeSection(middle_column, ideal_item_size_hint)
            middle_column = (self.nonvis_column_count - 1) / 2
            min_frame = current_frame - middle_column
            max_frame = current_frame + middle_column
            labels = [str(frame) if 0 <= frame <= self.video.frame_count else "" for frame in range(min_frame, max_frame + 1)]
            self.nonVisTable.setColumnCount(self.nonvis_column_count)
            header.setResizeMode(middle_column, QHeaderView.Stretch)
            self.nonVisTable.setHorizontalHeaderLabels(labels)
        # --------------------------------

        self.redrawNonVisTable(current_frame)

        #t1 = time.time() * 1000
        #print "displayNonVisAnnotation time", t1 - t0

    def redrawNonVisTable(self, current_frame=None):
        """
        Fills table with non-visual annotations
        :param current_frame: current frame
        """
        if not self.nonvis_annotation_enabled:
            return

        current_frame = self.player.getCurrentFrame() if current_frame is None else current_frame
        logger.debug("Called redrawNonVisTable for frame: %s", current_frame)

        self.nonVisTable.clearSelection()

        # ----- NON-VIS TABLE INITIALIZATION ------
        if self.selected_object_tuple and self.selected_object_tuple[0][0].type == self.NON_VIS_TYPE:
            non_visual_selected = True
            # if selected object is not active in displayed frame interval (edit mode)
            if self.selected_object_tuple[0] not in self.nonvis_objects_in_frame_range.itervalues():
                row_count = len(self.nonvis_objects_in_frame_range) + 1
            else:
                row_count = len(self.nonvis_objects_in_frame_range)
        else:
            non_visual_selected = False
            row_count = len(self.nonvis_objects_in_frame_range)
        self.nonVisTable.setRowCount(row_count)
        if row_count == 0:
            return
        # -------------------------------

        self.nonVisTable.setUpdatesEnabled(False)

        # creates empty rows*columns table for object id record
        # when user selects any cell, stored id and target frame on [row][col] position will be used
        self.nonvis_table_records = [[(None, None) for i in range(self.nonvis_column_count)] for j in range(row_count)]
        middle_column = (self.nonvis_column_count - 1) / 2

        # ------ FILL SELECTED NON-VIS ITEM  ------
        if non_visual_selected:
            an_object, start_frame, end_frame = self.selected_object_tuple[0]

            local_attributes = an_object.annotation_values_local()
            local_attributes = sorted(local_attributes, key=lambda attrib: attrib.frame_from)

            # row height init (Qt automatically sets row height to contents)
            #item = self.nonVisTable.item(0, 0)
            #if item is None:
            #    item = QTableWidgetItem()
            #    set_back = True
            #else:
            #    set_back = False
            #item.setText('\n')
            #if set_back:
            #    self.nonVisTable.setItem(0, 0, item)

            i = 0
            for column in range(self.nonvis_column_count):
                frame = current_frame - middle_column + column
                # check where another annotation value starts and change reference to another annotation value
                if i + 1 < len(local_attributes) and local_attributes[i + 1].frame_from <= frame:
                    i += 1

                item = self.nonVisTable.item(0, column)
                if item is None:
                    item = QTableWidgetItem()
                    set_back = True
                else:
                    set_back = False
                item.setText('\n')

                # *** COLORIZE ***
                if start_frame <= frame <= end_frame:
                    if column == middle_column:
                        #named_color = local_attributes[i].get_option(['gui', 'color', 'annotation_object_nonvisual_focus'])
                        named_color = self.default_colors['annotation_object_nonvisual_focus']
                        text_global, text_local = an_object.get_text(frame)
                        #text_global = ' ' if not text_global else text_global
                        #text_local = ' ' if not text_local else text_local
                        item.setText(text_global + '\n' + text_local)
                        self.nonvis_table_records[0][column] = (self.edited_id, frame)
                    else:
                        #named_color = local_attributes[i].get_option(['gui', 'color', 'annotation_object_nonvisual_focus'])
                        named_color = self.default_colors['annotation_object_nonvisual_focus']
                        self.nonvis_table_records[0][column] = (self.edited_id, frame)

                    if local_attributes[i].frame_from == frame:
                        #named_color = local_attributes[i].get_option(['gui', 'color', 'annotation_object_nonvisual_focus_not_interpolated'])
                        named_color = self.default_colors['annotation_object_nonvisual_focus_not_interpolated']

                elif 0 <= frame <= self.video.frame_count:
                    #named_color = local_attributes[i].get_option(['gui', 'color', 'annotation_object_nonvisual_edit'])
                    named_color = self.default_colors['annotation_object_nonvisual_edit']
                    self.nonvis_table_records[0][column] = (None, frame)
                else:
                    named_color = Qt.white
                    self.nonvis_table_records[0][column] = (None, None)

                # colorize item
                color = QColor(named_color)
                item.setBackground(QBrush(color))
                item.setForeground(QBrush(Qt.black))

                if set_back:
                    self.nonVisTable.setItem(0, column, item)

            row = 1
        # ---------------------------------------
        else:
            row = 0

        # ------- FILL TABLE WITH REST OF OBJECTS ----------
        for nonVisObjectTuple in self.nonvis_objects_in_frame_range.itervalues():
            #t0_1 = time.time() * 1000L

            an_object, start, stop = nonVisObjectTuple

            # do not draw selected object <= already drawn in first line
            if non_visual_selected and self.selected_object_tuple[0][0].id is an_object.id:
                continue

            local_attributes = an_object.annotation_values_local()
            local_attributes = sorted(local_attributes, key=lambda attrib: attrib.frame_from)
            local_attributes_len = len(local_attributes)

            # row height init (Qt automatically sets row height to contents)
            #item = QTableWidgetItem()
            #item.setText('\n')
            #self.nonVisTable.setItem(0, 0, item)

            i = 0
            for column in range(self.nonvis_column_count):
                frame = current_frame - middle_column + column
                # check where another annotation value starts and change reference to another annotation value
                if i + 1 < local_attributes_len and local_attributes[i + 1].frame_from <= frame:
                    i += 1

                # if some item is already in cell, use it and edit the item
                item = self.nonVisTable.item(row, column)
                if item is None:
                    item = QTableWidgetItem()
                    set_back = True
                else:
                    set_back = False
                item.setText('\n')

                # ACTIVE CELL
                if start <= frame <= stop:
                    if column == middle_column:
                        #named_color = local_attributes[i].get_option(['gui', 'color', 'annotation_object_nonvisual'])
                        named_color = self.default_colors['annotation_object_nonvisual']
                        text_global, text_local = an_object.get_text(frame)
                        #text_global = ' ' if not text_global else text_global
                        #text_local = ' ' if not text_local else text_local
                        item.setText(text_global + '\n' + text_local)
                        self.nonvis_table_records[row][column] = (an_object.id, frame)
                    else:
                        #named_color = local_attributes[i].get_option(['gui', 'color', 'annotation_object_nonvisual'])
                        named_color = self.default_colors['annotation_object_nonvisual']
                        self.nonvis_table_records[row][column] = (an_object.id, frame)

                    if local_attributes[i].frame_from == frame:
                        #named_color = local_attributes[i].get_option(['gui', 'color', 'annotation_object_nonvisual_not_interpolated'])
                        named_color = self.default_colors['annotation_object_nonvisual_not_interpolated']

                elif 0 <= frame <= self.video_frame_count:
                    named_color = Qt.white
                    self.nonvis_table_records[row][column] = (None, frame)
                else:
                    named_color = Qt.white
                    self.nonvis_table_records[row][column] = (None, None)

                # colorize item
                color = QColor(named_color)
                item.setBackground(QBrush(color))
                item.setForeground(QBrush(Qt.white))

                if set_back:
                    self.nonVisTable.setItem(row, column, item)
            row += 1

            #t1_1 = time.time() * 1000L
            #print "One nonvis object in loop", t1_1 - t0_1

        self.nonVisTable.setUpdatesEnabled(True)

    @Slot(int)
    def checkAndFillAnnotationTable(self, index):
        """
        Called when user changes current tab in toolsAndVideoTabWidget.
        If now is annotationTable visible, fill the table with data
        :param index: new tab index
        :type index: int
        """
        if index == 1 and not self.annotation_table_is_visible:
            self.annotation_table_is_visible = True

            # fill the table if player is not playing, else table will be filled when processObjects called
            if not self.player.isPlaying:
                self.annotationsTable.setRowCount(len(self.frame_cache))
                i = 0
                for key, value in self.frame_cache.iteritems():
                    an_object = value[0][0]
                    # *** add record to annotation table ***
                    object_comment = QTableWidgetItem(an_object.public_comment)
                    object_type = QTableWidgetItem(an_object.type)
                    object_id = QTableWidgetItem(str(an_object.id))
                    object_id.setTextAlignment(Qt.AlignCenter)
                    self.annotationsTable.setItem(i, 0, object_comment)
                    self.annotationsTable.setItem(i, 1, object_type)
                    self.annotationsTable.setItem(i, 2, object_id)
                    # **************************************
                    i += 1

        else:
            self.annotation_table_is_visible = False

    @Slot()
    def clearSelection(self, dont_redraw_nv_table=False):
        """
        Clears selected items and attribute table
        :param dont_redraw_nv_table: don't redraw non-visual table
        :type dont_redraw_nv_table: bool
        """
        if self.selected_object_tuple is None and self.edited_graphics_object is None:
            logger.debug("Clear selection called -> no object is selected")
            return

        logger.debug("Clear selection called, clearing selection.")

        # edit mode variables reset
        redraw_nonvis_table = not self.edited_is_visual       # selected item was non-visual -> redraw table
        self.closeEditMode()

        # scene selection reset
        self.scene.blockSignals(True)
        self.scene.clearSelection()
        self.scene.blockSignals(False)
        self.scene.markItems()

        self.selected_object_tuple = None
        self.selected_graphics_object = None
        self.displayed_object_id = None
        self.position_attrib_in_table_index = None
        self.position_an_value = None
        self.localTable.setRowCount(0)
        self.globalTable.setRowCount(0)
        self.local_attribs_in_table = []
        self.global_attribs_in_table = []
        self.parent().actionDelete.setEnabled(False)

        if redraw_nonvis_table and not dont_redraw_nv_table:
            self.redrawNonVisTable()

    @Slot()
    def userSelectedObjectByMouse(self):
        """
        When scene selection is changed, method is called to display values in tables or to clear selection
        """
        # check when prg. is closing, because garbage collector deletes binded c++ objects first
        if self.closing:
            return

        # get items mark as selected from the scene
        selectedItems = self.scene.selectedItems()

        # when selection changed, it will be emitted 3 times, like this:
        #   0) ..
        #   1) selectedItems = []
        #   2) selectedItems = [newlySelected, oldOneSelected]
        #   3) selectedItems = [newlySelected]
        #   => when already selected object in newly selected items -> ignore
        if self.selected_graphics_object in selectedItems:
            return

        if selectedItems:
            logger.debug("Scene selection changed -> new object will be set as selected")

            # set new selected object and refresh attribute table
            selectedGraphicsObject = selectedItems[0]
            objectID = selectedGraphicsObject.getId()
            try:
                self.selected_object_tuple = self.frame_cache[objectID]
            except KeyError:
                pass             # selected object is not added (active) for current frame (not cached)
            else:
                self.selected_graphics_object = selectedGraphicsObject   # store selected gra object

                self.startEditMode(selectedGraphicsObject)
                self.displayAttributes()
                self.parent().actionDelete.setEnabled(True)

                # show message in statusbar
                an_object = self.selected_object_tuple[0][0]
                self.statusbar.showMessage(self.selected_object_msg % (an_object.type, an_object.id), self.SHORT_MSG_DURATION)

    @Slot(int, int)
    def userSelectedObjectFromTable(self, row, column):
        """
        When user doubleclicks on row in table with annotations, current row annotation object is selected
        :type row: int
        :type column: int
        """
        logger.debug("User selected an. object from table, row: %s" % row)

        try:
            item_with_id = self.annotationsTable.item(row, 2)
            object_id = int(item_with_id.text())
            self.selected_object_tuple = self.frame_cache[object_id]
        except ValueError or TypeError:
            logger.exception("Entry on id position in annotation table is not a number")
            models.repository.logs.insert('gui.exception.select_obj_from_table_error',
                                          "Entry on id position in annotation table is not a number",
                                          annotator_id=self.user.id)
            return
        except KeyError:
            logger.exception("Given object (by id) is not in frame cache")
            return

        an_object = self.selected_object_tuple[0][0]

        if an_object.type == self.NON_VIS_TYPE:
            logger.debug("Selected object from table is non-visual")
            if self.edited_id is not None:
                was_visual = self.edited_is_visual
                self.closeEditMode()
                if was_visual:
                    # scene selection reset
                    self.scene.blockSignals(True)
                    self.scene.clearSelection()
                    self.scene.blockSignals(False)
                    self.scene.markItems()

            self.startEditMode(nonvis_id=object_id)
            self.displayAttributes()
            self.redrawNonVisTable()
            self.nonVisTable.scrollToTop()

        else:
            logger.debug("Selected object from table is visual")
            for item in self.scene_items:
                # find out which item points to selected graObject
                if item.getId() == an_object.id:
                    self.startEditMode(item)
                    self.selected_graphics_object = item
                    break

            frame = self.player.getCurrentFrame()
            self.reloadAndMarkSelectedObject(frame)
            self.displayAttributes()

        self.parent().actionDelete.setEnabled(True)
        self.statusbar.showMessage(self.selected_object_msg % (an_object.type, an_object.id), self.SHORT_MSG_DURATION)

    def reloadAndMarkSelectedObject(self, frame):
        """
        When new frame is delivered, selected item object needs to be manually colored as selected
        :param frame: current frame
        :type frame: int
        """

        # --- SELECTED NON-VISUAL OBJECT ---
        if self.edited_is_visual is False:
            logger.debug("Called markSelected object for non-visual object on frame: %s", frame)
            try:
                self.selected_object_tuple = self.frame_cache[self.edited_id]
            except KeyError:
                pass

        # --- SELECTED VISUAL OBJECT ---
        else:
            logger.debug("Called markSelected object for visual object on frame: %s", frame)

            # reset selection
            self.scene.blockSignals(True)
            self.scene.clearSelection()
            self.edited_graphics_object.setSelected(True)
            self.scene.blockSignals(False)

            # refresh selected object data
            try:
                self.selected_object_tuple = self.frame_cache[self.edited_id]
            except KeyError:
                pass             # selected object is not added (active) for current frame (not cached)

            # if object is not active in this frame, mark the object as inactive
            an_object = self.selected_object_tuple[0][0]
            if not an_object.is_active_in_frame(frame):
                self.edited_graphics_object.setActiveInFrame(False)
            else:
                self.edited_graphics_object.setActiveInFrame(True)

            self.scene.markItems()

    @Slot()
    def selectNonVisObject(self, target_id=None):
        """
        Sets non-visual annotation as selected, displays its attributes and seeks to target frame.
            a) Select object from table with row and column coordinates.
            b) Select object by id
        :param target_id: id of object we want to select
        """
        row = self.nonVisTable.currentRow()
        column = self.nonVisTable.currentColumn()
        logger.debug("Cell clicked, called selectNonVisObject on row: %s, column: %s", row, column)

        if not self.nonvis_table_records:
            logger.warning("No records in nonVisTableRecords table. Inappropriate method call.")
            return

        # reset selection if visual object was selected earlier or we want to set object by ID
        if self.edited_graphics_object or target_id is not None:
            self.clearSelection()                   # !! it causes redrawing non-vis table !!

        # --- SELECT OBJECT FROM TABLE ---
        if not target_id:
            # get annotation id and frame number if valid table cell has been selected
            object_id, frame = self.nonvis_table_records[row][column]

            if object_id is None:
                if self.selected_object_tuple and row == 0:
                    return

                logger.debug("No non-visual item selected")
                if self.selected_object_tuple:
                    self.clearSelection()
                return
        # --------------------------------

        # --- SELECT OBJECT BY ID ---
        else:
            object_id = target_id
            frame = self.player.getCurrentFrame()
        # ---------------------------

        try:
            self.selected_object_tuple = self.frame_cache[object_id]
        except KeyError:
            # selected object in not cached but is in displayed frame range
            # and will be selected after seek automatically
            pass

        else:
            # display msg in statusbar
            an_object = self.selected_object_tuple[0][0]
            self.statusbar.showMessage(self.selected_object_msg % (an_object.type, an_object.id),
                                       self.SHORT_MSG_DURATION)

        self.startEditMode(nonvis_id=object_id)

        # seeks to target frame
        if frame != self.player.getCurrentFrame():
            frame_duration = 1000.0 / self.video.fps
            new_time = frame * frame_duration
            self.player.seek(new_time)
        else:
            self.displayAttributes()
            self.redrawNonVisTable()

        self.nonVisTable.clearSelection()
        self.nonVisTable.scrollToTop()
        self.parent().actionDelete.setEnabled(True)

        logger.debug("Selected non visual annotation id: %s", object_id)

    @Slot(int, int)
    def extendNonVisAnnotation(self, row, column):
        """
        Extends selected non-visual annotation to corresponding with row/column.
        Called when user doubleClicks cell in nonVisTable.
        :type row: int
        :type column: int
        :return:
        """
        # wrong line doubleclicked or not in edit mode
        if row != 0 or self.edited_is_visual is not False or not self.selected_object_tuple:
            return

        frame = self.nonvis_table_records[row][column][1]
        an_object, start_frame, end_frame = self.selected_object_tuple[0]
        # if clicked out of range or on active part
        if frame is None or start_frame <= frame <= end_frame:
            return

        logger.debug("Extending selected non-visual annotation to frame: '%s'", frame)
        self.statusbar.showMessage(self.extending_nonvis_annotation_msg)

        # --- GET POSITION VALUE TO EXTEND ----
        position_attribute = repository.annotation_attributes.get_one_by_name(self.NON_VIS_POS_ATTRIB)
        local_values = an_object.annotation_values_local_grouped()
        position_values = local_values[position_attribute.id]

        if len(position_values) > 1:
            # extend current annotation
            position_values = sorted(position_values, key=lambda value: value.frame_from)
            if frame < start_frame:
                pos_value = position_values[0]
            else:
                pos_value = position_values[-1]
            add_new_value = False
        else:
            # new position value needs to be added
            add_new_value = True
        # ---------------------------------------

        try:
            if add_new_value:
                attrib = repository.annotation_attributes.get_one_by_name(self.NON_VIS_POS_ATTRIB)
                aValue = models.entity.AnnotationValue(frame_from=frame, value=None,
                                                       annotation_attribute=attrib, annotation_object=an_object,
                                                       created_by=self.user, modified_by=self.user)
            else:
                pos_value.frame_from = frame
                pos_value.modified_by = self.user
                pos_value.created_by = self.user
        except Exception:
            logger.exception("Failed to extend selected non-visual annotation")
            models.repository.logs.insert('gui.exception.extend_nonvis_an_error',
                                          "Failed to extend selected non-visual annotation",
                                          annotator_id=self.user.id)
            self.statusbar.showMessage(self.extending_nonvis_annotation_failed_msg)

        else:
            logger.debug("Selected non-visual annotation extended successfully")
            #self.buffer.resetBuffer(self.player.getCurrentFrame(), clear_object=(an_object.id, start_frame, end_frame))
            logger.debug("Resetting buffer from extendNonVisAnnotation")
            self.buffer.resetBuffer(self.player.getCurrentFrame(), clear_all=True)
            self.processObjects(draw=False)
            self.un_committed_changes = True

            self.statusbar.showMessage(self.add_new_attrib_successfully_msg, self.MSG_DURATION)



    def addNewGraphicsObject(self, graphics_object, an_obj_type, pos_attrib_name):
        """
        Adds new graphics annotation object of given type to database.
        :type graphics_object: tovian.gui.Components.graphics.AnnotationBaseClass
        :type an_obj_type: unicode
        :type pos_attrib_name: unicode
        """
        logger.debug("Added new object to scene. Trying to add the object to database")
        self.statusbar.showMessage(self.adding_new_object_msg)

        # create and add new object to db
        value = graphics_object.getOriginalPosInVideo(graphics_object.x(), graphics_object.y(), self.video.width, self.video.height)
        position_attribute = repository.annotation_attributes.get_one_by_name(pos_attrib_name)
        newObject = models.entity.AnnotationObject(type=an_obj_type, video=self.video, public_comment=u"",
                                                   created_by=self.user, modified_by=self.user)
        newPos = models.entity.AnnotationValue(frame_from=self.player.getCurrentFrame(), value=value,
                                               annotation_attribute=position_attribute, annotation_object=newObject,
                                               created_by=self.user, modified_by=self.user)
        try:
            models.database.db.session.add(newObject)
            models.database.db.session.flush()
        except:
            logger.exception("Adding new object to database failed")
            models.repository.logs.insert('gui.exception.adding_new_obj_to_db_error',
                                          "Adding new object to database failed",
                                          annotator_id=self.user.id)
            self.statusbar.showMessage(self.adding_new_object_failed_msg)
        else:
            logger.debug("New annotation object constructed successfully and added to database")
            logger.debug("Resetting buffer from addNewVisObject")
            self.buffer.resetBuffer(self.player.getCurrentFrame(), clear_all=True)
            graphics_object.setId(newObject.id)
            self.processObjects(draw=False)

            self.scene.blockSignals(True)
            self.scene.clearSelection()
            self.scene.blockSignals(False)
            graphics_object.setSelected(True)

            self.un_committed_changes = True
            self.statusbar.showMessage(self.adding_new_object_successfully_msg, self.MSG_DURATION)

    def addNewMaskObject(self, data):
        logger.debug("Adding new mask object to database")
        print "Implement adding new object to database!"

    @Slot(graphics.AnnotationBaseClass)
    def addedNewVisObject(self, graphics_object, obj_type):
        """
        When user draw new annotation object, method is called with this given object
        :param graphics_object: new drawn graphics object
        :type graphics_object: tovian.gui.Components.graphics.AnnotationBaseClass
        """
        if obj_type == graphics.Drawing.RECTANGLE:
            self.addNewGraphicsObject(graphics_object, an_obj_type=u'rectangle', pos_attrib_name=u'position_rectangle')
        elif obj_type == graphics.Drawing.CIRCLE:
            self.addNewGraphicsObject(graphics_object, an_obj_type=u'circle', pos_attrib_name=u'position_circle')
        elif obj_type == graphics.Drawing.POINT:
            self.addNewGraphicsObject(graphics_object, an_obj_type=u'point', pos_attrib_name=u'position_point')
        elif obj_type == graphics.Drawing.MASK:
            # get original coordinates
            view_size = self.scene.getVideoSize()
            view_width = view_size.width()
            view_height = view_size.height()
            orig_x = int(round((graphics_object.x() / float(view_width)) * self.video.width))
            orig_y = int(round((graphics_object.y() / float(view_height)) * self.video.height))
            orig_item_width = int(round((graphics_object.width / float(view_width)) * self.video.width))
            orig_item_height = int(round((graphics_object.height / float(view_height)) * self.video.height))

            # open mask editor
            self.scene.removeItem(graphics_object)
            self.openMaskEditor(orig_x, orig_y, orig_item_width, orig_item_height)
        else:
            raise NotImplementedError("Given type '%s' has not been implemented yet" % type(graphics_object))

    @Slot()
    def addNewNonVisObject(self):
        """
        Adds new non-visual annotation object to database.
        Called when user clicks non-visual tool button from toolbox.
        :return:
        """
        logger.debug("Adding new non-visual object to database")
        self.statusbar.showMessage(self.adding_new_nonvis_object_msg)

        # create and add new object to db
        value = None
        object_type = u'nonvisual'
        position_attrib_name = u'position_nonvisual'
        position_attribute = repository.annotation_attributes.get_one_by_name(position_attrib_name)

        new_object = models.entity.AnnotationObject(type=object_type, video=self.video, public_comment=u"",
                                                    created_by=self.user, modified_by=self.user)
        new_pos = models.entity.AnnotationValue(frame_from=self.player.getCurrentFrame(), value=value,
                                                annotation_attribute=position_attribute, annotation_object=new_object,
                                                created_by=self.user, modified_by=self.user)
        try:
            models.database.db.session.add(new_object)
            models.database.db.session.flush()
        except Exception:
            logger.exception("Adding new non-visual object to database failed")
            models.repository.logs.insert('gui.exception.adding_new_nonvis_obj_to_db_error',
                                          "Adding new non-visual object to database failed",
                                          annotator_id=self.user.id)
            self.statusbar.showMessage(self.adding_new_nonvis_object_failed_msg)
            return

        logger.debug("New non-visual object constructed and added to database successfully.")

        logger.debug("Resetting buffer from addNewNonVisObject")
        self.buffer.resetBuffer(self.player.getCurrentFrame(), clear_all=True)
        self.processObjects(draw=False)
        self.selectNonVisObject(target_id=new_object.id)
        self.displayAttributes()

        self.un_committed_changes = True
        self.statusbar.showMessage(self.adding_new_nonvis_object_successfully_msg, self.MSG_DURATION)

    def openMaskEditor(self, x, y, width, height, mask_data=None):
        """
        Opens mask editor with pixmap on given coordinates as background pixmap.
        :type x: int
        :type y: int
        :type width: int
        :type height: int
        :type mask_data: ???
        """
        pixmap = QPixmap.grabWidget(self.parent().videoWidget).scaled(self.video.width, self.video.height,
                                                                      Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        x1, y1 = x - width/2.0, y - height/2.0
        pixmap = pixmap.copy(x1, y1, width, height)

        maskDialog = MaskDialog(bgr_pixmap=pixmap, x=x, y=y, width=width, height=height, parent=self.parent())

        maskDialog.dataExported.connect(self.maskDataEdited)
        maskDialog.exec_()

    def deleteObject(self):
        """
        Deletes selected annotation object from database.
        """
        logger.debug("Called annotation object delete.")

        if self.selected_object_tuple is None:
            logger.warning("Inappropriate method call. No selected object to delete!")
            return

        an_object = self.selected_object_tuple[0][0]
        self.statusbar.showMessage(self.deleting_object_msg)

        try:
            models.database.db.session.delete(an_object)
            models.database.db.session.refresh(an_object)
        except Exception:
            logger.exception("Error when deleting object from database")
            models.repository.logs.insert('gui.exception.deleting_obj_from_db_error',
                                          "Error when deleting object from database",
                                          annotator_id=self.user.id)
            self.statusbar.showMessage(self.deleting_object_msg_failed)
        else:
            logger.debug("Object was deleted from database successfully")
            logger.debug("Resetting buffer from deleteObject")
            self.buffer.resetBuffer(self.player.getCurrentFrame(), clear_all=True)
            self.clearSelection(dont_redraw_nv_table=True)
            self.processObjects()

            self.un_committed_changes = True
            self.statusbar.showMessage(self.deleting_object_msg_successfully, self.MSG_DURATION)

    def deleteAttribute(self, attrib):
        """
        Deletes selected attribute from database
        :param attrib: selected annotation value
        :type attrib: tovian.models.entity.AnnotationValue
        """
        logger.debug("Delete attribute called")
        if self.selected_object_tuple is None:
            logger.debug("No selected object to delete attribute")
            return

        self.statusbar.showMessage(self.deleting_attrib_msg)
        an_object = self.selected_object_tuple[0][0]

        try:
            if attrib in models.database.db.session.new:
                logger.debug("Deleted attrib is in session.new => trying to expunge the attrib")
                models.database.db.session.expunge(attrib)
            else:
                logger.debug("Trying to delete the attrib")
                models.database.db.session.delete(attrib)
            #models.database.db.session.flush()
            models.database.db.session.refresh(an_object)
        except:
            logger.exception("Error when deleting an_value from database")
            models.repository.logs.insert('gui.exception.deleting_anvalue_from_db_error',
                                          "Error when deleting an_value from database",
                                          annotator_id=self.user.id)
            self.statusbar.showMessage(self.deleting_attrib_msg_failed)
        else:
            logger.debug("Attribute was deleted from database")
            logger.debug("Resetting buffer from deleteAttribute")
            self.buffer.resetBuffer(self.player.getCurrentFrame(), clear_all=True)
            self.processObjects()
            self.un_committed_changes = True
            self.statusbar.showMessage(self.deleting_attrib_msg_successfully, self.MSG_DURATION)

    def deleteAttribFromNonVisTable(self, frame, object_id):
        """
        Deletes annotation values of selected object for given frame.
        :param frame:
        :param object_id:
        :raise AttributeError:
        """
        if self.edited_id != object_id or not self.selected_object_tuple:
            raise AttributeError("Object_id and edited_id differs or no selected object at all")

        an_object = self.selected_object_tuple[0][0]
        l_values = an_object.annotation_values_local()
        l_values = sorted(l_values, key=lambda l_value: l_value.frame_from)

        to_delete = []
        for i in range(len(l_values)):
            value = l_values[i]
            if frame == value.frame_from:
                to_delete.append(value)
            elif frame < value.frame_from:
                break

        if not to_delete:
            logger.error("No annotation values found for given frame to delete")
            return

        logger.debug("Will be deleted '%s' values for selected object id %s", len(to_delete), an_object.id)
        self.statusbar.showMessage(self.deleting_attrib_msg)

        try:
            for value in to_delete:
                if value in models.database.db.session.new:
                    logger.debug("Deleted attrib is in session.new => trying to expunge the attrib")
                    models.database.db.session.expunge(value)
                else:
                    logger.debug("Trying to delete the attrib")
                    models.database.db.session.delete(value)
                #models.database.db.session.flush()
                models.database.db.session.refresh(an_object)
                l_values.remove(value)
        except:
            logger.exception("Error when deleting nonvis an_value from database")
            models.repository.logs.insert('gui.exception.deleting__nonvis_anvalue_from_db_error',
                                          "Error when deleting nonvis an_value from database",
                                          annotator_id=self.user.id)
            self.statusbar.showMessage(self.deleting_attrib_msg_failed)
        else:
            logger.debug("Attribute was deleted from database")
            current_frame = self.player.getCurrentFrame()
            frame_duration = 1000.0 / self.video.fps

            if current_frame < l_values[0].frame_from:
                logger.debug("Resetting buffer from deleteAttribFromNonVisTable")
                self.buffer.resetBuffer(l_values[0].frame_from, clear_all=True)
                new_time = l_values[0].frame_from * frame_duration
                self.player.seek(new_time)

            elif current_frame > l_values[-1].frame_from:
                logger.debug("Resetting buffer from deleteAttribFromNonVisTable")
                self.buffer.resetBuffer(l_values[-1].frame_from, clear_all=True)
                new_time = l_values[-1].frame_from * frame_duration
                self.player.seek(new_time)

            else:
                logger.debug("Resetting buffer from deleteAttribFromNonVisTable")
                self.buffer.resetBuffer(current_frame, clear_all=True)
                self.processObjects()

            self.un_committed_changes = True
            self.statusbar.showMessage(self.deleting_attrib_msg_successfully, self.MSG_DURATION)

    def goToNextObject(self):
        """
        Goes (seeks) to next object.
        If some object is selected, it goes to another object including currently displayed object
        Else, it goes to another object nearest object in different frame
        """
        frame = self.player.getCurrentFrame()
        logger.debug("Trying to jump to next annotation from frame '%s'...", frame)

        # if no object is selected
        if self.selected_object_tuple is None:
            data = self.video.annotation_object_next(frame)
        else:
            an_object = self.selected_object_tuple[0][0]
            data = self.video.annotation_object_next(frame, an_object)

        if data is None:
            logger.debug("There is no next annotation.")
            QApplication.beep()
            self.statusbar.showMessage(self.no_next_annotation_msg, self.SHORT_MSG_DURATION)
            return

        # seek to new annotation object
        next_object, frame_from, frame_to = data

        if self.selected_object_tuple:
            self.edited_id = next_object.id

            # delete current edited graObject from scene
            if self.edited_graphics_object:
                self.scene.removeItem(self.edited_graphics_object)
                self.edited_graphics_object = None

            if next_object.type == self.NON_VIS_TYPE:
                self.edited_is_visual = False
            else:
                self.edited_is_visual = True

        if frame_from > frame:
            frameDuration = 1000.0 / self.video.fps
            logger.debug("Seeking to next annotation on target frame: %s", frame_from)
            self.player.seek(frame_from * frameDuration)
        else:
            self.processObjects()

        self.player.resetPerFrameSlider()

    def goToPrevObject(self):
        """
        Goes (seeks) to previous object.
        If some object is selected, it goes to another object including currently displayed object
        Else, it goes to another object nearest object in different frame
        """
        frame = self.player.getCurrentFrame()
        logger.debug("Trying to jump to previous annotation from frame '%s'...", frame)

        # if no object is selected
        if self.selected_object_tuple is None:
            data = self.video.annotation_object_previous(frame)
        else:
            an_object = self.selected_object_tuple[0][0]
            data = self.video.annotation_object_previous(frame, an_object)

        if data is None:
            logger.debug("There is no previous annotation.")
            QApplication.beep()
            self.statusbar.showMessage(self.no_prev_annotation_msg, self.SHORT_MSG_DURATION)
            return

        # seek to new annotation object
        next_object, frame_from, frame_to = data

        if self.selected_object_tuple:
            self.edited_id = next_object.id

            # delete current edited graObject from scene
            if self.edited_graphics_object:
                self.scene.removeItem(self.edited_graphics_object)
                self.edited_graphics_object = None

            if next_object.type == self.NON_VIS_TYPE:
                self.edited_is_visual = False
            else:
                self.edited_is_visual = True

        if frame_to < frame:
            frameDuration = 1000.0 / self.video.fps
            logger.debug("Seeking to previous annotation on target frame: %s", frame_from)
            self.player.seek(frame_from * frameDuration)
        else:
            self.processObjects()

        self.player.resetPerFrameSlider()

    def startEditMode(self, graphics_object=None, nonvis_id=None):
        """
        Starts edit mode, which allows to change the start and end of annotations
        :param graphics_object: pointer to graphics object on scene
        :type graphics_object: tovian.gui.Components.graphics.AnnotationBaseClass
        :param nonvis_id: id of non-visual object
        :type nonvis_id: int
        """
        # --- FOR VISUAL OBJECTS ----
        if graphics_object is not None:
            logger.debug("Initializing edit mode for visual object id: %s", graphics_object.getId())
            # selected already selected object
            if graphics_object is self.edited_graphics_object:
                logger.debug("Selected object already in edit mode")
                return

            # remove previous object from scene if object is not active in current frame
            if self.edited_graphics_object is not None:
                if not self.edited_id in self.frame_cache.keys():
                    # object is not active in current frame => remove
                    self.scene.blockSignals(True)
                    self.scene.removeItem(self.edited_graphics_object)
                    self.scene.blockSignals(False)
                else:
                    # object is active in current frame => move object to sceneItems list
                    self.scene_items.append(self.edited_graphics_object)

            # set new graphics object as edited
            self.edited_graphics_object = graphics_object
            self.edited_id = graphics_object.getId()
            if not self.edited_is_visual:
                self.redrawNonVisTable()        # reset non-vis table
            self.edited_is_visual = True

            # remove from object from others -> it wont be deleted on new redraw until new object is selected
            if self.edited_graphics_object in self.scene_items:
                self.scene_items.remove(self.edited_graphics_object)

        # --- FOR NON-VISUAL OBJECTS ---
        elif nonvis_id is not None:
            logger.debug("Initializing edit mode for non-visual object id: %s", nonvis_id)
            self.edited_id = nonvis_id
            self.edited_is_visual = False

    def closeEditMode(self):
        """
        When user hits enter or escape in scene, it will close edit mode and refresh objects
        """
        logger.debug("Resetting edit mode")

        if self.edited_is_visual:
            # object is not active in current frame => remove
            if not self.edited_id in self.frame_cache.keys():
                self.scene.removeItem(self.edited_graphics_object)

            # object is still active in current frame => move object to sceneItems list
            else:
                self.scene_items.append(self.edited_graphics_object)

        self.edited_graphics_object = None
        self.edited_id = None
        self.edited_manual_pos_set = False
        self.edited_is_visual = None

    def getAllowedAttributes(self, is_local):
        """
        Returns list of allowed local/global annotation attributes
        :type is_local: bool
        :return: list of allowed local/global annotation attributes
        :rtype: list of tovian.models.entity.AnnotationAttribute
        """
        an_object = self.selected_object_tuple[0][0]
        allowed_attributes = []

        if is_local:
            for attrib in self.video.annotation_attributes:
                if not (attrib.is_global or attrib.name in self.VIS_OBJ_POS_ATTRIBS
                        or an_object.type != attrib.annotation_object_type):
                    allowed_attributes.append(attrib)
        else:
            for attrib in self.video.annotation_attributes:
                if not (not attrib.is_global or attrib.name in self.VIS_OBJ_POS_ATTRIBS
                        or an_object.type != attrib.annotation_object_type):
                    allowed_attributes.append(attrib)

        return allowed_attributes

    @Slot()
    def addNewLocalAttribute(self):
        """
        When user hits local attribute table context menu or add button
        Dialog with remaining (not added) attributes is shown
        """
        logger.debug("Add new local attribute initialized")
        self.statusbar.showMessage(self.add_new_attrib_select_msg)
        dialog = AttribSelectionDialog(self.remaining_local_attribs, self.parent())
        dialog.attributeSelected.connect(self.addAttributeToDB)
        logger.debug("Opening dialog with allowed attributes")
        dialog.show()

    @Slot()
    def addNewGlobalAttribute(self):
        """
        Called when user hits global attribute table context menu or add button
        Dialog with remaining (not added) attributes is shown
        """
        logger.debug("Add new global attribute initialized")
        self.statusbar.showMessage(self.add_new_attrib_select_msg)
        dialog = AttribSelectionDialog(self.remaining_global_attribs, self.parent())
        dialog.attributeSelected.connect(self.addAttributeToDB)
        logger.debug("Opening dialog with allowed attributes")
        dialog.show()

    @Slot(models.entity.AnnotationAttribute)
    def addAttributeToDB(self, attrib):
        """
        Called when user selects from allowed attributes. Adds to database value of given attribute.
        :type attrib: tovian.models.entity.AnnotationAttribute
        """
        logger.debug("New attribute selected, initializing adding procedure to db")

        # when edit mode - if selected an_object is not active in frame -> add new value
        self.processChanges()

        an_object = self.selected_object_tuple[0][0]
        self.statusbar.showMessage(self.add_new_attrib_writing_msg)

        # init value depending specified data type
        if attrib.allowed_values:
            value = attrib.allowed_values[0]
        elif attrib.data_type == u"unicode":
            value = u""
        elif attrib.data_type == u"int":
            value = 0
        elif attrib.data_type == u"float":
            value = 0.0
        elif attrib.data_type == u"tuple":
            value = ()
        elif attrib.data_type == u"list":
            value = []
        elif attrib.data_type == u"str":
            value = ""
        else:
            value = u""

        logger.debug("Attribute type is '%s'" % type(value))

        try:
            # add attribute value to database
            if attrib.is_global:
                logger.debug("Adding new global attribute '%s'" % attrib.name)
                an_value = models.entity.AnnotationValue(value=value, annotation_attribute=attrib,
                                                         annotation_object=an_object, created_by=self.user,
                                                         modified_by=self.user)
            else:
                logger.debug("Adding new local attribute '%s'" % attrib.name)
                an_value = models.entity.AnnotationValue(frame_from=self.player.getCurrentFrame(), value=value,
                                                         annotation_attribute=attrib, annotation_object=an_object,
                                                         created_by=self.user, modified_by=self.user)
            models.database.db.session.flush()
        except Exception:
            logger.exception("Adding new an_value %s failed", attrib.name)
            models.repository.logs.insert('gui.exception.adding_anvalue_to_db_error',
                                          "Adding new an_value %s failed" % attrib.name,
                                          annotator_id=self.user.id)
            self.statusbar.showMessage(self.add_new_attrib_failed_msg)
        else:
            self.processObjects()
            self.statusbar.showMessage(self.add_new_attrib_successfully_msg, self.MSG_DURATION)

            logger.debug("New attribute added successfully")

    @Slot(graphics.AnnotationBaseClass, QPointF)
    def graphicsItemGeometryChanged(self, gra_object, pos):
        """
        When position or size of graphicsItem on scene changed, method is called to edit position value
        :type gra_object: tovian.gui.Components.graphics.AnnotationBaseClass
        :type pos: PySide.QtCore.QPointF
        """
        if self.selected_object_tuple is None or self.edited_manual_pos_set or self.displayed_object_id != gra_object.data(0):
            self.edited_manual_pos_set = False
            return

        an_object = self.selected_object_tuple[0][0]
        pos_value_item = self.localTable.cellWidget(self.position_attrib_in_table_index, 1)
        gra_object_type = type(gra_object)

        pos_value_item.blockSignals(True)
        if gra_object_type is graphics.AnnotationRect:
            x1, y1, x2, y2 = gra_object.getOriginalPosInVideo(pos.x(), pos.y(), self.video.width, self.video.height)
            pos_value = (x1, y1, x2, y2)
            pos_value_item.setText("(%d, %d, %d, %d)" % (x1, y1, x2, y2))
        elif gra_object_type is graphics.AnnotationCircle:
            x, y, r = gra_object.getOriginalPosInVideo(pos.x(), pos.y(), self.video.width, self.video.height)
            pos_value = (x, y, r)
            pos_value_item.setText("(%d, %d, %d)" % (x, y, r))
        elif gra_object_type is graphics.AnnotationPoint:
            x, y = gra_object.getOriginalPosInVideo(pos.x(), pos.y(), self.video.width, self.video.height)
            pos_value = (x, y)
            pos_value_item.setText("(%d, %d)" % (x, y))
        else:
            pos_value_item.blockSignals(False)
            raise NotImplementedError("Implement item type support")
        pos_value_item.blockSignals(False)

        frame = self.player.getCurrentFrame()
        # ADD NEW VALUE
        if not an_object.is_active_in_frame(frame):
            # get attrib type
            if an_object.type == u'rectangle':
                positionAttribName = u'position_rectangle'
            elif an_object.type == u'circle':
                positionAttribName = u'position_circle'
            elif an_object.type == u'point':
                positionAttribName = u'position_point'
            else:
                raise NotImplementedError("Given type has not been implemented yet")

            # ADD NEW VALUE TO DB FOR CURRENT FRAME
            pos_attrib = repository.annotation_attributes.get_one_by_name(positionAttribName)
            position = models.entity.AnnotationValue(frame_from=frame,
                                                     value=pos_value,
                                                     annotation_attribute=pos_attrib,
                                                     annotation_object=an_object,
                                                     created_by=self.user,
                                                     modified_by=self.user)
            models.database.db.session.flush()

            self.buffer.resetBuffer(frame, clear_all=True)
            self.processObjects(draw=False)

        # EDIT CURRENT VALUE
        else:
            self.position_an_value.value = pos_value
            if self.position_an_value.is_interpolated:
                logger.debug("Value is interpolated, adding session and flushing...")
                self.position_an_value.database_session_add()
                models.database.db.session.flush()
                gra_object.drawSolid()

        self.statusbar.showMessage(self.geometry_changes_processed_msg, self.SHORT_MSG_DURATION)
        self.un_committed_changes = True

    def applyChanges(self, i, local):
        """
        Process changes in given attribute table for given attributes
        :param i: start row in attribute table
        :param local: if local attrib or global
        :type i: int
        :type local: bool
        :return: something changed ?
        :rtype: bool
        """
        change = False

        frame = self.player.getCurrentFrame()
        an_object = self.selected_object_tuple[0][0]
        is_active = an_object.is_active_in_frame(frame)
        changed_pairs = []

        # get changes type - local or global
        if local:
            an_values_list = self.selected_object_tuple[1]
            table = self.localTable
        else:
            an_values_list = self.selected_object_tuple[2]
            table = self.globalTable

        # ITERATE OVER ROWS AND FIND CHANGES
        for an_value in an_values_list:
            # ignore non-vis position value <- hidden
            if an_value.annotation_attribute.name == u'position_nonvisual':
                continue

            widget = table.cellWidget(i, 1)

            # allowed values combobox
            if isinstance(widget, QComboBox):
                table_value_str = table.cellWidget(i, 1).currentText()
                table_value_parsed = table_value_str

            # lineEdit value - common value
            elif isinstance(widget, QLineEdit):
                table_value_str = widget.text()
                table_value_parsed = self.parseValue(table_value_str, an_value)       # parse value from table

                if table_value_parsed is None:
                    QApplication.beep()     # error beep
                    logger.debug("Edited values '%s' has wrong syntax for data type '%s'",
                                 table_value_str, type(an_value.value))
                    orig_text = an_value.value
                    orig_text = orig_text if isinstance(orig_text, basestring) else unicode(orig_text)
                    widget.blockSignals(True)
                    widget.setText(orig_text)
                    widget.blockSignals(False)

                    self.statusbar.showMessage(self.syntax_error_msg % (table_value_str, type(an_value.value)))
                    i += 1
                    continue

            else:
                logger.error("Unknown table item on row %s for attrib name '%s'", i, an_value.annotation_attribute.name)
                i += 1
                continue

            # IF VALUE HAS BEEN CHANGED
            if an_value.value != table_value_parsed:

                # if an_object is active or global, write changes
                if is_active or not local:
                    logger.debug("%s has been changed, now writing changes...", an_value.annotation_attribute.name)
                    an_value.value = table_value_parsed
                    an_value.modified_by = self.user

                    # needs to be add as new value to SQLAlchemy if interpolated
                    if an_value.is_interpolated:
                        logger.debug("Adding value to session -> flushing...")
                        an_value.database_session_add()
                        models.database.db.session.flush()

                        graObjects = self.scene.selectedItems()
                        if graObjects:
                            graObjects[0].drawSolid()

                    # update completer
                    try:
                        attrib_name = an_value.annotation_attribute.name
                        completer = self.completers[attrib_name]
                    except KeyError:
                        pass
                    else:
                        string_list = completer.model().stringList()
                        if not table_value_parsed in string_list:
                            logger.debug("Updating completer for attribute '%s'", attrib_name)

                            # model update crashes the Python => create whole new completer
                            string_list.append(table_value_parsed)
                            completer = QCompleter(string_list, self)
                            completer.setCaseSensitivity(Qt.CaseInsensitive)
                            self.completers[an_value.annotation_attribute.name] = completer

                # if not, changes cannot be written because an. value is not from current frame
                else:
                    changed_pairs.append((an_value, table_value_parsed))

                change = True
            i += 1

        if changed_pairs:
            return changed_pairs
        else:
            return change

    def applyGlobalAttribChanges(self, an_object):
        """
        Checks record in global attributes table and process changes
        :return: if some change were proceed
        :rtype : bool or list
        """
        change = False

        # FOR PUBLIC_COMMENT, no need for parsing, comment is string
        comment_widget = self.globalTable.cellWidget(0, 1)
        if comment_widget is not None:
            tableValueParsed = comment_widget.text()       # load value from table
            # if has been current table value changed
            if an_object.public_comment != tableValueParsed:
                an_object.public_comment = tableValueParsed
                logger.debug("Public comment has been changed")
                change = True

        # process rest of attributes and return if something has been edited
        attrib_changes = self.applyChanges(4, local=False)
        return attrib_changes or change

    def applyLocalAttribChanges(self):
        """
        Checks record in local attributes table and process changes
        :return: if some change were proceed
        :rtype : bool or list
        """
        return self.applyChanges(0, local=True)

    @staticmethod
    def parseValue(table_value_str, attrib):
        """
        Called to parse text from table to correct format as same as records in database
        :param table_value_str: item text from table
        :param attrib: pointer to attribute
        :type table_value_str: unicode
        :type attrib: tovian.models.entity.AnnotationValue
        :return: parsed value or None
        :rtype: object
        """
        # if table value data type differs from dbValue data type
        # --- only strings equals strings(unicode), others records needs to be parsed to correct data type
        if not isinstance(table_value_str, type(attrib.value)):
            # normalizes strings - numbered vale is assumed
            table_value_str = table_value_str.replace(' ', '')

            # tries to parse value to valid Python literal
            try:
                table_value_parsed = ast.literal_eval(table_value_str)
            except Exception:
                logger.debug("Error when parsing python literal. Value '%s' has wrong syntax." % table_value_str)
                return None

            # parsed value is in different type than database value
            if not type(table_value_parsed) is type(attrib.value):
                logger.debug("Parsed value is not the same type as db value: %s <-> %s"
                             % (type(table_value_parsed), type(attrib.value)))
                return None

            # check if given tuple or list has correct length
            if type(table_value_parsed) is tuple or type(table_value_parsed) is list:
                if not len(table_value_parsed) == len(attrib.value):
                    logger.debug("Length of parsed list/tuple doesn't math db value length")
                    return None
        else:
            table_value_parsed = table_value_str

        return table_value_parsed

    @Slot()
    def processChanges(self):
        """
        Called when user hit the commit button or manually to process data in attribute table and commit changes
        :return: if some change were proceed
        :rtype : bool
        """
        # if called during processObjects or no object is selected -> ignore
        if self.processing_objects or self.selected_object_tuple is None:
            return False

        logger.debug("Processing changes...")
        an_object = self.selected_object_tuple[0][0]

        # process changes
        self.processing_changes = True
        changed_local_values = self.applyLocalAttribChanges()
        global_changed = self.applyGlobalAttribChanges(an_object)
        self.processing_changes = False

        # if true, means that object not active in frame has been changed
        if isinstance(changed_local_values, list):
            logger.debug("Changes were detected but object is not active in frame => adding new value")
            frame = self.player.getCurrentFrame()

            # get attrib type
            if an_object.type == u'rectangle':
                positionAttribName = u'position_rectangle'
            elif an_object.type == u'circle':
                positionAttribName = u'position_circle'
            elif an_object.type == u'point':
                positionAttribName = u'position_point'
            else:
                raise NotImplementedError("Given type has not been implemented yet")

            # ADD NEW VALUE TO DB FOR CURRENT FRAME
            graObject = self.edited_graphics_object
            pos_attrib = repository.annotation_attributes.get_one_by_name(positionAttribName)
            value = graObject.getOriginalPosInVideo(graObject.x(), graObject.y(),
                                                    self.video.width, self.video.height)
            position = models.entity.AnnotationValue(frame_from=frame,
                                                     value=value,
                                                     annotation_attribute=pos_attrib,
                                                     annotation_object=an_object,
                                                     created_by=self.user,
                                                     modified_by=self.user)
            models.database.db.session.flush()

            self.buffer.resetBuffer(frame, clear_all=True)
            self.processObjects(draw=False)                 # an. values reload

            # PROCESS CHANGES
            local_values = self.selected_object_tuple[1]
            for old_an_value, new_value in changed_local_values:
                for an_value in local_values:
                    if an_value.annotation_attribute.name == old_an_value.annotation_attribute.name:
                        logger.debug("%s has been changed - writing changes", an_value.annotation_attribute.name)

                        an_value.value = new_value
                        an_value.modified_by = self.user

                        if an_value.is_interpolated:
                            logger.debug("Changed value is interpolated - adding to session and flushing...")
                            an_value.database_session_add()
                            models.database.db.session.flush()

                            graObjects = self.scene.selectedItems()
                            if graObjects:
                                graObjects[0].drawSolid()

                        # update completer
                        try:
                            attrib_name = an_value.annotation_attribute.name
                            completer = self.completers[attrib_name]
                        except KeyError:
                            pass
                        else:
                            string_list = completer.model().stringList()
                            if not new_value in string_list:
                                logger.debug("Updating completer for attribute '%s'", attrib_name)
                                string_list.append(new_value)
                                # model update crashes the Python, so create whole new completer
                                self.completers[an_value.annotation_attribute.name] = QCompleter(string_list, self)
                        break
            changes = True
        else:
            changes = changed_local_values or global_changed

        if changes:
            self.statusbar.showMessage(self.changes_processed_msg, self.SHORT_MSG_DURATION)
            self.processObjects()   # redraw
            self.un_committed_changes = True

        return changes

    @Slot(buffer, bool)
    def maskDataEdited(self, data, is_new):
        """
        When mask editor is closed and some data has been modified,
        this method is called to save modified data to an_object
        :type data: buffer
        :type is_new: bool
        """
        if is_new:
            self.addNewMaskObject(data)
        else:
            print "Implement data editing"

        print "Exported data recieved"

    def commit(self):
        """
        Called when user hit the save button or manually to process data in attribute table and commit changes
        """
        logger.debug("Commit method called")
        self.committing = True
        self.statusbar.showMessage(self.committing_msg)
        # self.processChanges()

        logger.debug("Committing changes")
        try:
            models.database.db.session.commit()
            models.repository.logs.insert('gui.save', annotator_id=self.user.id)
        except Exception:
            logger.exception("Error when committing new data")
            models.repository.logs.insert('gui.exception.commit_error',
                                          "Error when committing new data",
                                          annotator_id=self.user.id)
            self.statusbar.showMessage(self.committing_failed_msg)
            QMessageBox(QMessageBox.Critical, "Save error", self.committing_failed_msg).exec_()
        else:
            self.statusbar.showMessage(self.committing_successfully_msg, self.MSG_DURATION)
            self.un_committed_changes = False
            logger.debug("Resetting buffer from commit")
            self.buffer.resetBuffer(self.player.getCurrentFrame(), clear_all=True)
            self.committing = False

    def undo(self):
        """
        Reverts all changes from last db.session.commit() calling
        """
        logger.debug("Undo method called")
        self.statusbar.showMessage(self.reverting_msg)

        self.parent().playPauseBtn.setEnabled(False)
        try:
            models.database.db.session.rollback()
        except Exception:
            logger.exception("Error when reverting changes from database")
            models.repository.logs.insert('gui.exception.undo_error',
                                          "Error when reverting changes from database",
                                          annotator_id=self.user.id)
            self.statusbar.showMessage(self.reverting_failed_msg)
            # TODO send by error msg
            QMessageBox(QMessageBox.Critical, "Undo error", self.reverting_failed_msg).exec_()
        else:
            self.un_committed_changes = False
            logger.debug("Resetting buffer from undo")
            self.buffer.resetBuffer(self.player.getCurrentFrame(), clear_all=True)
            self.clearSelection(dont_redraw_nv_table=True)
            self.processObjects()

            self.statusbar.showMessage(self.reverting_successfully_msg, self.MSG_DURATION)
            logger.debug("Data reverted successfully")
        finally:
            self.parent().playPauseBtn.setEnabled(True)

    def initCompleters(self):
        """
        Setup completer for each annotation attribute. Later used for an_value and autocomplete.
        """
        position_attribs = (u'position_rectangle', u'position_circle',
                            u'position_point', u'position_ellipse', u'position_nonvisual')

        for an_attrib in self.video_attributes:
            if an_attrib.name in position_attribs or an_attrib.allowed_values:
                continue

            strings = an_attrib.autocomplete_values()

            if strings:
                completer = QCompleter(strings, self)
                completer.setCaseSensitivity(Qt.CaseInsensitive)

                self.completers[an_attrib.name] = completer