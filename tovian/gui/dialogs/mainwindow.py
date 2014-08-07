# -*- coding: utf-8 -*-

"""
Main application dialog.
"""

import os
import logging
import datetime
import time
import json

from PySide.QtGui import *
from PySide.QtCore import *
from PySide.phonon import Phonon

from tovian.gui.forms import mainform
from tovian.gui.components import videoplayer
from tovian.gui.components import graphics
from tovian.gui.components import eventfilters
from tovian.gui.components import buffer
from ..components.annotation import Annotation
from tovian import models

from . import goto
from . import mask


logger = logging.getLogger(__name__)
logger.debug('Import ' + __name__)


class MainApp(QMainWindow, mainform.Ui_MainWindow):
    """
    Main GUI app of Tovian.
    """

    windows_title = u"Tovian - Video Annotation Tool"
    draw_rect_msg = u"Draw where you want to put the rectangle or press Escape to cancel."
    draw_circle_msg = u"Draw where you want to put the circle or press Escape to cancel."
    draw_ellipse_msg = u"Draw where you want to put the ellipse or press Escape to cancel."
    draw_point_msg = u"Select where you want to put the point or press Escape to cancel."

    error_title = u"Error occurred"
    closing_buffer_error = u"Unable to close buffer thread safely. Thread must be terminated.\n\n" \
                           u"Please, report this error!"

    video_is_ready_msg = u"video is ready..."
    video_error_occurred_msg = u"Error occurred. Please, check the log file for more information."
    commit_on_close_msg = u"There are some unsaved changes."
    commit_on_close_detailed_msg = u"Do you want to save last changes? Otherwise, all changes will be lost!"
    commit_on_close_title = u"Save changes?"
    buffering_msg = u"Buffering..."
    position_memorized_msg = u"Current video position has been memorized"

    passive_db_access_msg = u"<b>Inactive database access</b><br/>Total access count: %s"
    active_db_access_msg = u"<b>Active database access</b><br/>Total access count: %s"
    closing_buffer_msg = u"Trying to close buffer..."
    terminating_buffer_msg = u"Unable to close buffer, trying to terminate buffer thread..."

    add_new_local_attrib_btn = u"Add new local attribute"
    add_new_local_attrib_tooltip = u"Pick new local attribute from allowed attributes"
    add_new_global_attrib_btn = u"Add new global attribute"
    add_new_global_attrib_tooltip = u"Pick new global attribute from allowed attributes"
    delete_attrib_btn = u"Delete attribute"
    delete_attrib_tooltip = u"Delete selected attribute"

    geometryReady = Signal()
    newObjectDrawn = Signal(graphics.AnnotationBaseClass, int)
    zoomChanged = Signal(float)
    windowClosed = Signal()

    DB_CHECK_PERIOD = 1000
    MSG_DURATION = 5000
    SHORT_MSG_DURATION = 2000

    SMALL_FONT = 10
    NORMAL_FONT = 12
    LARGE_FONT = 14

    def __init__(self, user, video, rootPath):
        """
        :type user: tovian.models.entity.Annotator
        :type video: tovian.models.entity.Video
        :type rootPath: str
        """
        super(MainApp, self).__init__()
        self.user = user
        self.video = video
        self.rootPath = rootPath
        self.am_I_Drawing = False
        self.geometry_initialized = False
        self.drawing_class = None
        self.selected_tool_btn = None
        self.zoom = 1.0
        self.application_initialized = False
        self.application_init_video_pause = False
        self.nonvis_annotation_enabled = True
        self.signal_mapper = QSignalMapper()
        self.buffer = buffer.Buffer(self.video, self.user.id)
        self.buffer_thread = QThread()
        self.buffer.moveToThread(self.buffer_thread)
        self.dbCheckTimer = QTimer()
        self.fps = self.video.fps
        self.frame_count = self.video.frame_count
        self.video_duration = self.video.duration
        self.memorized_pos = None

        # setup gui
        self.setupUi(self)
        self.initializeAllowedTools()
        self.setDefaultWindowSize()
        self.setupContextMenu()
        self.annotation = Annotation(self)      # annotation user controller
        self.setupFilters()
        self.setupSignals()

        QTimer().singleShot(0, self.afterInit)          # called when whole dialog is loaded .. 100ms delay
        logger.debug("Main GUI initialized")

        self.maskToolBtn.setVisible(False)

    def setupUi(self, parent):
        """
        Overridden setup UI method.
        :type parent: MainApp
        """
        super(MainApp, self).setupUi(parent)
        self.videoNameLlb.setText(str(self.video.name))
        self.zoomlSlider.setMinimumWidth(50)
        self.userLbl.setText(self.user.email)
        self.setWindowFlags(self.windowFlags() ^ Qt.WindowContextHelpButtonHint)
        self.setWindowTitle(self.windows_title)

        # fill video properties
        self.videoTable.setItem(0, 1, QTableWidgetItem(self.video.name))
        self.videoTable.setItem(1, 1, QTableWidgetItem(self.video.filename))
        self.videoTable.setItem(2, 1, QTableWidgetItem(str(self.video.width) + "x" + str(self.video.height)))
        self.videoTable.setItem(3, 1, QTableWidgetItem("%s fps (%s frames)" % (self.video.fps, self.video.frame_count)))
        timeInSec = self.video.duration
        ms = round((timeInSec - int(timeInSec)) * 1000)
        if ms >= 1000:
            ms = 0
            timeInSec += 1
        hms = time.strftime('%H:%M:%S', time.gmtime(timeInSec))
        self.timeLbl.setText("%s:%03d" % (hms, ms))
        self.videoTable.setItem(4, 1, QTableWidgetItem("%s.%03d" % (hms, ms)))
        self.videoTable.setItem(5, 1, QTableWidgetItem("No" if self.video.is_finished else "Yes"))

        # setup annotation table geometry
        header = self.annotationsTable.horizontalHeader()
        header.setResizeMode(0, QHeaderView.Interactive)
        header.setResizeMode(1, QHeaderView.Stretch)
        header.setResizeMode(2, QHeaderView.ResizeToContents)
        self.annotationsTable.setColumnWidth(0, 230)
        self.annotationsTable.setColumnWidth(2, 35)

        # setup nonVis annotation table
        self.nonVisTable.setMouseTracking(True)
        font = self.nonVisTable.font()
        font.setPixelSize(self.SMALL_FONT)
        self.nonVisTable.setFont(font)
        header = self.nonVisTable.verticalHeader()
        header.setResizeMode(QHeaderView.ResizeToContents)
        header = self.nonVisTable.horizontalHeader()
        header.setResizeMode(QHeaderView.Fixed)

        # graphicsView init
        self.scene = graphics.GraphicsScene(self)
        self.graphicsView.setStyleSheet("background: #000000")
        self.graphicsView.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.graphicsView.setScene(self.scene)
        self.graphicsView.resizeEvent = self.graphicsViewResizeEvent
        self.graphicsView.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.videoGridLayout.setAlignment(self.graphicsView, Qt.AlignCenter)

        # Setup multimedia player
        path = os.path.join(self.rootPath, 'data', 'video', self.video.filename)
        self.audioOuptut = Phonon.AudioOutput(Phonon.MusicCategory, self)
        self.videoWidget = Phonon.VideoWidget()
        self.player = videoplayer.VideoPlayer(self, path)
        Phonon.createPath(self.player, self.audioOuptut)
        Phonon.createPath(self.player, self.videoWidget)
        self.playerProxy = self.scene.addWidget(self.videoWidget)
        self.playerProxy.setVisible(False)
        self.scene.video_size = self.playerProxy.size()

        # setup player controls
        self.mainSeekSlider = videoplayer.MainVideoSeeker(self)
        self.mainSeekSlider.setMinimumWidth(100)
        self.volumeSlider = Phonon.VolumeSlider(self.audioOuptut)
        self.volumeSlider.setFixedWidth(100)
        self.mainVideoBarHLayout.addWidget(self.mainSeekSlider)
        self.mainVideoBarHLayout.addWidget(self.volumeSlider)
        self.playPauseBtn.setFocus()
        self.stopBtn.setVisible(False)      # if not hide and later show -> paint update of player wont work properly!

        # status bar
        self.fpsLabel = QLabel("Frame #0")
        self.statusbar.addPermanentWidget(self.fpsLabel)

        # icons
        zoom_icon = QPixmap(":/icons/icons/zoom.png").scaled(QSize(16, 16), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        self.zoomLbl.setPixmap(zoom_icon)
        db_icon = QPixmap(":/icons/icons/database.png").scaled(QSize(16, 16), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        self.db_status = QLabel()
        self.db_status.setPixmap(db_icon)
        self.db_status.setMinimumWidth(25)
        self.db_status.setAlignment(Qt.AlignCenter)
        self.statusbar.addPermanentWidget(self.db_status)

    def setDefaultWindowSize(self):
        """
        Choose as default size of dialog 80% size of available screen.
        Proper dialog size will be adjusted later depending on video aspect ratio.
        """
        logger.debug("Resizing dialog to default size, 80% of available screen size")
        availableGeometry = QCoreApplication.instance().desktop().availableGeometry()
        width = availableGeometry.width() - 0.2 * availableGeometry.width()
        height = availableGeometry.height() - 0.2 * availableGeometry.height()
        self.resize(width, height)

    def setupSignals(self):
        """
        Setup widget signal/slot mechanism.
        """
        # map clicked signal from toolbar so signal sender can be identified
        self.rectToolBtn.clicked.connect(self.signal_mapper.map)
        self.circleToolBtn.clicked.connect(self.signal_mapper.map)
        self.ellipseToolBtn.clicked.connect(self.signal_mapper.map)
        self.pointToolBtn.clicked.connect(self.signal_mapper.map)
        self.nonVisToolBtn.clicked.connect(self.annotation.addNewNonVisObject)
        # self.maskToolBtn.clicked.connect(self.annotation.openMaskEditor)
        self.maskToolBtn.clicked.connect(self.signal_mapper.map)
        self.signal_mapper.setMapping(self.rectToolBtn, graphics.Drawing.RECTANGLE)
        self.signal_mapper.setMapping(self.circleToolBtn, graphics.Drawing.CIRCLE)
        self.signal_mapper.setMapping(self.maskToolBtn, graphics.Drawing.MASK)
        self.signal_mapper.setMapping(self.pointToolBtn, graphics.Drawing.POINT)
        self.signal_mapper.mapped.connect(self.clicked)
        # QGraphicsView mouse event handle
        self.scene.btnForDrawingPressed.connect(self.mousePressWhenDrawing)
        self.scene.btnForDrawingMoved.connect(self.mouseMoveEventInScene)
        self.scene.btnForDrawingReleased.connect(self.mouseReleaseEventInScene)
        self.scene.mouseZoom.connect(self.setZoom)
        self.scene.noObjectIsSelected.connect(self.annotation.clearSelection)
        self.scene.selectionChanged.connect(self.annotation.userSelectedObjectByMouse)
        self.scene.geometryChanged.connect(self.annotation.graphicsItemGeometryChanged)

        self.zoomChanged.connect(self.scene.scaleItemsPen)
        self.zoomlSlider.valueChanged.connect(self.setZoom)
        self.geometryReady.connect(self.resetDialogOptimalGeometry)
        #self.geometryReady.connect(self.setVideoToFit)

        self.newObjectDrawn.connect(self.annotation.addedNewVisObject)
        # player
        self.playPauseBtn.clicked.connect(self.player.playPauseVideo)
        self.frameLeftBtn.clicked.connect(self.player.seekFrameBackward)
        self.frameRightBtn.clicked.connect(self.player.seekFrameForward)
        self.skipSecFwdBtn.clicked.connect(self.player.seekSecForward)
        self.skipSecBackBtn.clicked.connect(self.player.seekSecBackward)
        self.skipLeftBtn.clicked.connect(self.annotation.goToPrevObject)
        self.skipRightBtn.clicked.connect(self.annotation.goToNextObject)
        self.stopBtn.clicked.connect(self.player.stopVideo)
        self.perFrameSlider.valueChanged.connect(self.player.perFrameSeek)
        self.player.playing.connect(self.videoIsPlaying)
        self.player.paused.connect(self.videoIsPaused)
        self.player.stopped.connect(self.videoIsStopped)
        self.player.errorOccurred.connect(self.runtimeErrorOccurred)
        self.player.newFrameTimer.timeout.connect(self.annotation.processObjects)
        self.player.seeking.connect(self.annotation.processObjects)
        self.player.stopped.connect(self.annotation.clearSelection)
        self.player.errorOccurred.connect(self.annotation.clearSelection)
        self.player.paused.connect(self.mainSeekSlider.synchronize)
        # setup actions
        self.actionAbout.triggered.connect(self.displayAboutDialog)
        self.actionKeyboard_shortcuts.triggered.connect(self.displayKeyboardShortcutsDialog)
        self.actionCommit.triggered.connect(self.commitClicked)
        self.actionUndo_changes.triggered.connect(self.undoClicked)
        self.actionTake_a_snapshot.triggered.connect(self.player.takeSnapshot)
        self.actionFit_to_video.triggered.connect(self.fitDialogToVideoSize)
        self.actionDelete.triggered.connect(self.annotation.deleteObject)
        self.actionFontSmall.triggered.connect(self.changeAnLabelsFontSizeToSmall)
        self.actionFontNormal.triggered.connect(self.changeAnLabelsFontSizeToNormal)
        self.actionFontLarge.triggered.connect(self.changeAnLabelsFontSizeToLarge)
        self.actionFontNone.triggered.connect(self.changeAnLabelsFontSizeToNone)
        self.actionGo_to.triggered.connect(self.displayGoToDialog)
        self.actionMark_current_frame.triggered.connect(self.memoryCurrentPos)
        # annotation
        self.commitBtn.clicked.connect(self.commitClicked)
        self.undoBtn.clicked.connect(self.undoClicked)
        self.dbCheckTimer.timeout.connect(self.checkDatabase)
        self.annotation.error.connect(self.runtimeErrorOccurred)
        self.annotationsTable.cellClicked.connect(self.annotation.userSelectedObjectFromTable)
        self.nonVisTable.cellDoubleClicked.connect(self.annotation.extendNonVisAnnotation)
        self.toolsAndVideoTabWidget.currentChanged.connect(self.annotation.checkAndFillAnnotationTable)
        # BUFFER
        self.buffer_thread.started.connect(self.buffer.initBuffer)
        self.buffer_thread.finished.connect(self.buffer.bufferFinished)
        self.buffer_thread.terminated.connect(self.buffer.bufferTerminated)
        self.buffer.buffering.connect(self.displayBufferingMsg)
        self.buffer.initialized.connect(self.bufferInitialized)
        self.buffer.buffered.connect(self.statusbar.clearMessage)

    def setupFilters(self):
        """
        Setup event filters for catching events
        """
        # setup filters
        mainUiEventFilter = eventfilters.GlobalFilter(self)
        # attributeTableFilter = eventfilters.AttributeTableFilter(self)
        perFrameSeekerFilter = eventfilters.PerFrameSeekerFilter(self)
        nonVisTableFilter = eventfilters.NonVisTableFilter(self)

        self.installEventFilter(mainUiEventFilter)
        self.rectToolBtn.installEventFilter(mainUiEventFilter)
        self.circleToolBtn.installEventFilter(mainUiEventFilter)
        self.pointToolBtn.installEventFilter(mainUiEventFilter)
        self.graphicsView.installEventFilter(mainUiEventFilter)
        self.perFrameSlider.installEventFilter(perFrameSeekerFilter)
        # self.localTable.installEventFilter(attributeTableFilter)
        # self.globalTable.installEventFilter(attributeTableFilter)
        self.nonVisTable.viewport().installEventFilter(nonVisTableFilter)

        mainUiEventFilter.escapePressed.connect(self.annotation.clearSelection)
        mainUiEventFilter.escapePressed.connect(self.scene.clearSelection)
        mainUiEventFilter.escapePressed.connect(self.endDrawing)
        mainUiEventFilter.playKeyPressed.connect(self.player.playPauseVideo)
        mainUiEventFilter.stopKeyPressed.connect(self.player.stopVideo)
        mainUiEventFilter.volumeUpKeyPressed.connect(self.player.volumeUp)
        mainUiEventFilter.volumeDownKeyPressed.connect(self.player.volumeDown)
        mainUiEventFilter.muteKeyPressed.connect(self.player.mute)
        # attributeTableFilter.enterPressed.connect(self.annotation.processChanges)
        perFrameSeekerFilter.LMouseRelease.connect(self.player.perFrameSliderLMouseReleased)
        perFrameSeekerFilter.LMousePress.connect(self.player.perFrameSliderLMousePressed)
        nonVisTableFilter.LMouseRelease.connect(self.annotation.selectNonVisObject)

    def setupContextMenu(self):
        """
        Creates context menu for widgets
        """
        self.addLocalAttribAction = QAction(self.add_new_local_attrib_btn, self)
        self.addLocalAttribAction.setShortcut(QKeySequence.New)
        self.addLocalAttribAction.setIcon(QIcon(":/icons/icons/add_attrib.png"))
        self.addLocalAttribAction.setStatusTip(self.add_new_local_attrib_tooltip)
        self.addLocalAttribAction.setEnabled(False)

        self.addGlobalAttribAction = QAction(self.add_new_global_attrib_btn, self)
        self.addGlobalAttribAction.setShortcut(QKeySequence.New)
        self.addGlobalAttribAction.setIcon(QIcon(":/icons/icons/add_attrib.png"))
        self.addGlobalAttribAction.setStatusTip(self.add_new_global_attrib_tooltip)
        self.addGlobalAttribAction.setEnabled(False)

        self.deleteAttribAction = QAction(self.delete_attrib_btn, self)
        self.deleteAttribAction.setShortcut(QKeySequence.Delete)
        self.deleteAttribAction.setIcon(QIcon(":/icons/icons/delete.png"))
        self.deleteAttribAction.setStatusTip(self.delete_attrib_tooltip)
        self.deleteAttribAction.setEnabled(False)

        self.localTable.setContextMenuPolicy(Qt.CustomContextMenu)
        self.globalTable.setContextMenuPolicy(Qt.CustomContextMenu)
        self.nonVisTable.setContextMenuPolicy(Qt.CustomContextMenu)
        self.localTable.customContextMenuRequested.connect(self.createLocalAttribContextMenu)
        self.globalTable.customContextMenuRequested.connect(self.createGlobalAttribContextMenu)
        self.nonVisTable.customContextMenuRequested.connect(self.createNonVisTableContextMenu)

    @Slot(QPoint)
    def createLocalAttribContextMenu(self, pos):
        """
        Constructs custom context menu local attribute table depending on mouse click position
        :param pos: right-mouseclick pos
        :type pos: PySide.QtCore.QPoint
        """

        separator = QAction(self)
        separator.setSeparator(True)
        menu = QMenu(self.localTable)
        menu.addAction(self.addLocalAttribAction)
        menu.addAction(separator)
        menu.addAction(self.deleteAttribAction)
        self.deleteAttribAction.setEnabled(False)

        # if it has been right-clicked on not-interpolated attribute => enable delete action
        item = self.localTable.itemAt(pos)
        if item is not None:
            attrib = self.annotation.local_attribs_in_table[item.row()]
            if type(attrib) is models.entity.AnnotationValue and not attrib.is_interpolated:
                self.deleteAttribAction.setEnabled(True)

        logger.debug("Opening local attrib table context menu.")
        chosenAction = menu.exec_(self.localTable.viewport().mapToGlobal(pos))
        if chosenAction is self.deleteAttribAction:
            self.annotation.deleteAttribute(attrib)
        elif chosenAction is self.addLocalAttribAction:
            self.annotation.addNewLocalAttribute()

    @Slot(QPoint)
    def createGlobalAttribContextMenu(self, pos):
        """
        Constructs custom context menu for global attribute table depending on mouse click position
        :param pos: right-mouseclick pos
        :type pos: PySide.QtCore.QPoint
        """

        separator = QAction(self)
        separator.setSeparator(True)
        menu = QMenu(self.localTable)
        menu.addAction(self.addGlobalAttribAction)
        menu.addAction(separator)
        menu.addAction(self.deleteAttribAction)
        self.deleteAttribAction.setEnabled(False)

        # if it has been right-clicked on not-interpolated attribute => enable delete action
        item = self.globalTable.itemAt(pos)
        if item is not None:
            attrib = self.annotation.global_attribs_in_table[item.row()]
            if type(attrib) is models.entity.AnnotationValue and not attrib.is_interpolated:
                self.deleteAttribAction.setEnabled(True)

        logger.debug("Opening global attrib table context menu.")
        chosenAction = menu.exec_(self.globalTable.viewport().mapToGlobal(pos))
        if chosenAction is self.deleteAttribAction:
            self.annotation.deleteAttribute(attrib)
        elif chosenAction is self.addGlobalAttribAction:
            self.annotation.addNewGlobalAttribute()

    @Slot(QPoint)
    def createNonVisTableContextMenu(self, pos):
        """
        Constructs custom context menu non-visual table depending on mouse click position
        :param pos: right-mouseclick pos
        :type pos: PySide.QtCore.QPoint
        """
        # if context menu is invoked on selected non-vis object on not-interpolated value
        if self.annotation.edited_is_visual is False and self.annotation.selected_object_tuple:
            item = self.nonVisTable.itemAt(pos)
            if item is not None:
                row = item.row()
                column = item.column()
                if row == 0:
                    object_id, frame = self.annotation.nonvis_table_records[row][column]
                    if object_id is not None and frame is not None:
                        menu = QMenu(self.nonVisTable)
                        menu.addAction(self.deleteAttribAction)
                        self.deleteAttribAction.setEnabled(True)
                        logger.debug("Opening context menu on item in nonVisTable")
                        chosenAction = menu.exec_(self.nonVisTable.viewport().mapToGlobal(pos))
                        if chosenAction is self.deleteAttribAction:
                            logger.debug("Chosen to delete the annotation value from context menu")
                            self.annotation.deleteAttribFromNonVisTable(frame, object_id)

    def initializeAllowedTools(self):
        """
        Depending on allowed tools for the video method hides other tools
        :raise NotImplementedError: When unknown tool found.
        """
        logger.debug("Initializing allowed annotation tools")
        allowedTools = self.video.allowed_annotation_object_types.split(' ')
        rectToolBtnVisibility = False
        circleToolBtnVisibility = False
        pointToolBtnVisibility = False
        ellipseToolBtnVisibility = False
        nonVisToolBtnVisibility = False

        for tool in allowedTools:
            if tool == u'rectangle':
                rectToolBtnVisibility = True
            elif tool == u'circle':
                circleToolBtnVisibility = True
            elif tool == u'point':
                pointToolBtnVisibility = True
            elif tool == u'nonvisual':
                nonVisToolBtnVisibility = True
            else:
                raise NotImplementedError("Unimplemented tool '%s' found in allowed tools", tool)

        if not rectToolBtnVisibility:
            self.rectToolBtn.setVisible(False)
        if not circleToolBtnVisibility:
            self.circleToolBtn.setVisible(False)
        if not pointToolBtnVisibility:
            self.pointToolBtn.setVisible(False)
        if not ellipseToolBtnVisibility:
            self.ellipseToolBtn.setVisible(False)
        if not nonVisToolBtnVisibility:
            self.nonVisTable.setVisible(False)
            self.nonVisToolBtn.setVisible(False)
            self.nonvis_annotation_enabled = False

    def disableAnnotationTools(self):
        """
        Sets all annotation tools as disabled to user interaction
        """
        logger.debug("Disabling annotation tools")
        self.rectToolBtn.setEnabled(False)
        self.circleToolBtn.setEnabled(False)
        self.ellipseToolBtn.setEnabled(False)
        self.pointToolBtn.setEnabled(False)
        self.nonVisToolBtn.setEnabled(False)

    def enableAnnotationTools(self):
        """
        Sets all annotation tools as enabled to user interaction
        """
        logger.debug("Enabling annotation tools")
        self.rectToolBtn.setEnabled(True)
        self.circleToolBtn.setEnabled(True)
        self.ellipseToolBtn.setEnabled(True)
        self.pointToolBtn.setEnabled(True)
        self.nonVisToolBtn.setEnabled(True)

    def initDrawing(self, message):
        """
        Initializes drawing object, displays statusbar message.
        :param message: Message displayed in statusbar
        :type message: str
        """
        self.am_I_Drawing = True
        self.scene.drawing_mode = True
        self.statusbar.showMessage(message)
        self.selected_tool_btn.setDown(True)
        # self.drawing_class = graphics.Drawing(self.scene, self.selectedToolId, self.video.get_option(), self)
        self.drawing_class = graphics.Drawing(self.scene, self.selectedToolId, self.video.get_option(['gui', 'color']), self)
        self.scene.setMovable(False)
        self.graphicsView.setCursor(Qt.CrossCursor)
        self.playerProxy.setCursor(Qt.CrossCursor)
        logger.debug("Drawing initialized")

    def endDrawing(self, cancel=True):
        """
        Ends or cancels drawing procedure.
        :param cancel: cancel flag
        :type cancel: bool
        """
        self.am_I_Drawing = False
        self.scene.drawing_mode = False
        self.statusbar.clearMessage()
        if self.selected_tool_btn:
            self.selected_tool_btn.setDown(False)
        self.scene.setMovable(True)
        self.graphicsView.setCursor(Qt.ArrowCursor)
        self.playerProxy.setCursor(Qt.ArrowCursor)

        if not self.drawing_class:
            return None

        if cancel:
            logger.debug("Canceling drawing")
            self.drawing_class.cancel()
        else:
            self.newObjectDrawn.emit(self.drawing_class.graphics_object, self.selectedToolId)

        self.drawing_class = None
        self.selected_tool_btn = None
        self.selectedToolId = None
        logger.debug("Drawing ended")

    def setVideoToFit(self):
        """
        Set video position and size to fit graphicsView and video aspect ratio.
        """
        logger.debug("Fitting video widgets to available space")

        videoRatio = self.video.width / float(self.video.height)        # video aspect ratio
        cellRect = self.gridLayout.cellRect(1, 0)                       # cell with video and nonVisTable

        # calculate optimal width/height
        width = cellRect.width()
        height = round(width / videoRatio)

        # check if new height is not bigger than available space
        if self.nonVisTable.isVisible():
            maxHeight = self.rightSplitter.height() - self.nonVisTable.height() - self.gridLayout.verticalSpacing()
        else:
            maxHeight = self.rightSplitter.height()

        if height > maxHeight:
            # calculate new width from maximum available height
            height = maxHeight
            width = videoRatio * height

        oldSize = self.scene.getVideoSize()
        border = 2                                              # 1 px both side
        width = width - border if width > 0 else 0
        height = height - border if height > 0 else 0

        if oldSize.width() != width or oldSize.height() != height:
            self.scene.video_size = QSize(width, height)
            self.graphicsView.setMaximumSize(width, height)
            self.playerProxy.resize(width, height)          # minus border size
            self.scene.video_size = QSize(width, height)
            self.scene.setSceneRect(QRect(0, 0, width, height))
            self.playerProxy.setPos(0, 0)

            if self.zoom == 1.0:
                self.graphicsView.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                self.graphicsView.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            else:
                self.graphicsView.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
                self.graphicsView.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
                self.scene.scaleItemsPen(self.zoom)

            self.scene.viewResized.emit()

    def resizeEvent(self, event):
        """
        Called when user resizes Main window.
        :type event: PySide.QtGui.QResizeEvent
        :rtype : None
        """
        super(MainApp, self).resizeEvent(event)
        self.setVideoToFit()

    def fitDialogToVideoSize(self):
        """
        Fits dialog to its optimal size - removes unused space
        Partly keeps window position
        """
        self.resetDialogOptimalGeometry(repos_window=False)

    def resetDialogOptimalGeometry(self, repos_window=True):
        """
        Called to set dialog size to fit graphicsView depending on video aspect ratio.
        It will remove empty space and center the dialog and center the dialog
        :param repos_window: center dialog
        :type repos_window: bool
        """
        logger.debug("Resizing dialog to its optimal geometry")

        empty_x_space = self.videoGridLayout.cellRect(0, 0).width() - self.graphicsView.width()
        empty_y_space = self.videoGridLayout.cellRect(0, 0).height() - self.graphicsView.height()

        empty_x_space = 0 if empty_x_space < 0 else empty_x_space
        empty_y_space = 0 if empty_y_space < 0 else empty_y_space

        if empty_x_space != 0 or empty_y_space != 0:
            self.resize(self.width() - empty_x_space, self.height() - empty_y_space)

            if repos_window:
                # center the dialog
                frect = self.frameGeometry()
                frect.moveCenter(QDesktopWidget().availableGeometry().center())
                self.move(frect.topLeft())

    @Slot(QResizeEvent)
    def graphicsViewResizeEvent(self, event):
        """
        Relinked QGraphicsView.resizeEvent. Used to detect when geometry of graphicsView is initialized
        :type event: PySide.QtGui.QResizeEvent
        """
        QGraphicsView.resizeEvent(self.graphicsView, event)     # parent method

        # check when graphicsView has non-zero size value (has been initialized)
        if not self.geometry_initialized and not event.size() == QSize(0, 0):
            self.geometry_initialized = True
            self.geometryReady.emit()

    def closeEvent(self, event):
        """
        Called when main window is closed. App needs to close buffer thread first!
        :type event: PySide.QtGui.QCloseEvent
        """
        logger.debug("Close event called")

        # if there were some uncommitted changes
        if self.annotation.un_committed_changes:
            logger.debug("There are some uncommitted changes, opening message dialog for user to decide")

            # crates the question dialog
            dialog = QMessageBox(QMessageBox.Question, self.commit_on_close_title, "")
            dialog.setWindowIcon(self.windowIcon())
            dialog.setText("<b>" + self.commit_on_close_msg + "</b>")
            dialog.setInformativeText(self.commit_on_close_detailed_msg)

            save = dialog.addButton(QMessageBox.Save)
            dontSave = dialog.addButton(QMessageBox.Discard)
            cancel = dialog.addButton(QMessageBox.Cancel)

            dialog.exec_()

            # commit or don't close the window
            if dialog.clickedButton() is save:
                logger.debug("User decided to save changes, calling commit procedure")
                self.annotation.commit()
            elif dialog.clickedButton() is cancel:
                logger.debug("User decided to don't close the window")
                event.ignore()
                return
            else:
                logger.debug("User decided to ignore changes and close the window")

        self.closeBuffer()
        event.accept()

        self.windowClosed.emit()

    def closeBuffer(self):
        """
        Tries to terminate buffering thread "safely" for 10 sec
        """
        logger.debug("Trying to close buffer thread")
        self.statusbar.showMessage(self.closing_buffer_msg)

        self.annotation.closing = True
        self.buffer_thread.quit()
        self.buffer_thread.wait(5000)

        if not self.buffer_thread.isFinished():
            logger.error("Unable to close buffer thread normally")
            self.statusbar.showMessage(self.terminating_buffer_msg)
            self.buffer_thread.setTerminationEnabled(True)
            self.buffer_thread.terminate()

    @Slot()
    def changeAnLabelsFontSizeToSmall(self):
        """
        Action triggered by user to change font size of annotation labels to small
        """
        self.changeAnLabelsFontSize(self.SMALL_FONT)

    @Slot()
    def changeAnLabelsFontSizeToNormal(self):
        """
        Action triggered by user to change font size of annotation labels to normal
        """
        self.changeAnLabelsFontSize(self.NORMAL_FONT)

    @Slot()
    def changeAnLabelsFontSizeToLarge(self):
        """
        Action triggered by user to change font size of annotation labels to large
        """
        self.changeAnLabelsFontSize(self.LARGE_FONT)

    @Slot()
    def changeAnLabelsFontSizeToNone(self):
        """
        Action triggered by user to hide annotation labels
        """
        self.changeAnLabelsFontSize(None)

    def changeAnLabelsFontSize(self, size):
        """
        Change annotation object label font size
        :param size: size in px or None if hidden
        :type size: int or None
        """
        logger.debug("Changing an_object label font size to value '%s'", size)
        self.annotation.label_font_size = size
        if self.player.isPaused:
            self.annotation.processObjects()

    @Slot()
    def checkDatabase(self):
        """
        Periodically checks when was the last database access and then sets status icon as "active or passive"
        """
        lastAccess = (datetime.datetime.now() - models.database.db.profiler['last_access']).total_seconds()

        if lastAccess > 1:
            self.db_status.setEnabled(False)
            tooltip = self.passive_db_access_msg % models.database.db.profiler['sql_count']
        else:
            self.db_status.setEnabled(True)
            tooltip = self.active_db_access_msg % models.database.db.profiler['sql_count']

        self.db_status.setToolTip(tooltip)

    @Slot()
    def commitClicked(self):
        """
        When commit button is clicked, temporary disables buttons, calls commit method and re-enables buttons
        """
        self.commitBtn.setEnabled(False)
        self.actionCommit.setEnabled(False)
        self.annotation.commit()
        self.commitBtn.setEnabled(True)
        self.actionCommit.setEnabled(True)

    @Slot()
    def undoClicked(self):
        """
        When undo button is clicked, temporary disables buttons, calls undo method and re-enables buttons
        """
        self.undoBtn.setEnabled(False)
        self.actionUndo_changes.setEnabled(False)
        self.annotation.undo()
        self.undoBtn.setEnabled(True)
        self.actionUndo_changes.setEnabled(True)

    @Slot(int)
    def setZoom(self, newZoom):
        """
        Zoom the graphicsView.
        :type newZoom: int
        :param newZoom: value in %
        """
        # if mouse wheel zoom
        if newZoom < 100:
            value = ((newZoom/100.0) + self.zoom) * 100
            if value < self.zoomlSlider.minimum():
                newValue = self.zoomlSlider.minimum() / 100.0
                scaleValue = newValue / self.zoom
                self.zoom = self.zoomlSlider.minimum() / 100.0
            elif value > self.zoomlSlider.maximum():
                newValue = self.zoomlSlider.maximum() / 100.0
                scaleValue = newValue / self.zoom
                self.zoom = self.zoomlSlider.maximum() / 100.0
            else:
                newValue = (newZoom/100.0) + self.zoom
                scaleValue = newValue / self.zoom
                self.zoom += newZoom/100.0

            self.zoomlSlider.blockSignals(True)
            self.zoomlSlider.setValue(self.zoom * 100)
            self.zoomlSlider.blockSignals(False)

        # QSlider zoom
        else:
            scaleValue = (newZoom/100.0) / self.zoom
            self.zoom = newZoom/100.0

        self.graphicsView.scale(scaleValue, scaleValue)
        self.zoomValueLbl.setText(str(self.zoom*100) + "%")

        if self.zoom > 1:
            self.graphicsView.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            self.graphicsView.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        else:
            self.graphicsView.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.graphicsView.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        items = self.scene.selectedItems()
        if items:
            item = items[0]
            self.graphicsView.centerOn(item)
        self.zoomChanged.emit(self.zoom)

        if self.zoom == 1:
            self.graphicsView.centerOn(self.playerProxy)

    @Slot(int)
    def clicked(self, buttonID):
        """
        Annotation toolbar button clicked slot.
        :param buttonID: sender id
        :type buttonID: int
        """
        self.selectedToolId = buttonID
        if buttonID == graphics.Drawing.RECTANGLE:
            self.selected_tool_btn = self.rectToolBtn
            message = self.draw_rect_msg
        elif buttonID == graphics.Drawing.CIRCLE:
            self.selected_tool_btn = self.circleToolBtn
            message = self.draw_circle_msg
        elif buttonID == graphics.Drawing.MASK:
            self.selected_tool_btn = self.maskToolBtn
            message = "Draw mask region"
        elif buttonID == graphics.Drawing.POINT:
            self.selected_tool_btn = self.pointToolBtn
            message = self.draw_point_msg
        else:
            return True

        self.initDrawing(message)

    @Slot()
    def videoIsStopped(self):
        """
        When video is stopped, deletes annotation objects from scene, resets mainSeeker, disables annotation tools,
        resets buffer, disables view interactivity
        """
        if not self.application_initialized:
            return

        logger.debug("Setting GUI to video stopped state, buffering to frame 0")
        self.fpsLabel.setText("Frame #0")

        self.mainSeekSlider.blockSignals(True)
        self.mainSeekSlider.setValue(0)
        self.mainSeekSlider.blockSignals(False)
        self.scene.clearScene()

        self.scene.view.setInteractive(False)
        self.undoBtn.setEnabled(False)
        self.actionUndo_changes.setEnabled(False)
        self.skipRightBtn.setEnabled(False)
        self.skipLeftBtn.setEnabled(False)
        self.perFrameSlider.setEnabled(False)
        self.frameRightBtn.setEnabled(False)
        self.frameLeftBtn.setEnabled(False)

        self.disableAnnotationTools()
        self.annotation.buffer.resetBuffer(0)

    @Slot()
    def videoIsPaused(self):
        """
        When video is paused, enable view interactivity and annotation tools
        """
        if not self.application_initialized and self.application_init_video_pause:
            logger.debug("Video paused, still initializing =>"
                         "seeking back to frame 0 after initialization.")
            self.player.seek(0)
            self.application_initialized = True

        logger.debug("Setting GUI to video paused state.")
        self.perFrameSlider.setEnabled(True)
        self.frameRightBtn.setEnabled(True)
        self.frameLeftBtn.setEnabled(True)
        self.scene.view.setInteractive(True)
        self.undoBtn.setEnabled(True)
        self.actionUndo_changes.setEnabled(True)
        self.skipRightBtn.setEnabled(True)
        self.skipLeftBtn.setEnabled(True)
        self.enableAnnotationTools()

        if self.player.getCurrentFrame() != 0:
            logger.debug("Calling processObjects() because of current time synchronization")
            self.annotation.processObjects()
            self.player.videoTimeLabelSynch(self.player.currentTime())

    @Slot()
    def videoIsPlaying(self):
        """
        When player is playing, disable view interactivity and annotation tools
        """
        if not self.application_initialized:
            self.application_init_video_pause = True
            self.player.pause()
            logger.debug("Video is playing, but initializing video => pausing the video.")

        self.perFrameSlider.setEnabled(True)
        self.perFrameSlider.setEnabled(False)
        self.frameRightBtn.setEnabled(False)
        self.frameLeftBtn.setEnabled(False)
        self.undoBtn.setEnabled(False)
        self.actionUndo_changes.setEnabled(False)
        self.skipRightBtn.setEnabled(False)
        self.skipLeftBtn.setEnabled(False)
        self.scene.view.setInteractive(False)
        self.disableAnnotationTools()

    @Slot()
    def bufferInitialized(self):
        """
        Called first time when annotation objects are loaded tu buffer
        Plays the player and then immediately is player stopped and seeked back to frame '0'
        """
        logger.debug("Buffer initialized for frame 0.")
        self.dbCheckTimer.start(self.DB_CHECK_PERIOD)

        logger.debug("Loading video player component (play -> pause) ...")
        self.playerProxy.setVisible(True)     # if not hide and than show -> paint update of player wont work properly!
        self.player.play()

    @Slot()
    def afterInit(self):
        """
        Method called from timer after dialog is fully initialized
        """
        self.setVideoToFit()
        self.scene.viewResized.connect(self.annotation.displayNonVisAnnotations)

        logger.debug("Starting buffer thread...")
        self.buffer_thread.start()

    @Slot()
    def runtimeErrorOccurred(self):
        """
        When video returns error, hides video widget (currentFrame), shows error message,
        deletes annotation objects from scene, resets mainSeeker, disables annotation tools,
        resets buffer, disables view interactivity
        """
        logger.debug("Setting GUI to video runtime error occurred mode")

        # TODO receive error message and display it on messagebox
        self.mainSeekSlider.blockSignals(True)
        self.mainSeekSlider.setValue(0)
        self.mainSeekSlider.blockSignals(False)
        self.playerProxy.setVisible(False)
        self.scene.clearScene()
        self.scene.view.setInteractive(False)

        # scene error message
        videoSize = self.scene.getVideoSize()
        viewWidth = videoSize.width()
        viewHeight = videoSize.height()
        self.sceneText = QGraphicsTextItem(self.video_error_occurred_msg)
        self.sceneText.setDefaultTextColor(QColor(Qt.gray))
        self.sceneText.setOpacity(0.5)
        font = self.sceneText.font()
        font.setPixelSize(16)
        self.sceneText.setFont(font)
        centerX = (viewWidth - self.sceneText.boundingRect().width()) / 2.0
        centerY = (viewHeight - self.sceneText.boundingRect().height()) / 2.0
        self.sceneText.setPos(centerX, centerY)
        self.sceneText.setVisible(True)
        self.scene.addItem(self.sceneText)

        self.perFrameSlider.setEnabled(False)
        self.frameRightBtn.setEnabled(False)
        self.frameLeftBtn.setEnabled(False)
        self.playPauseBtn.setEnabled(False)
        self.stopBtn.setEnabled(False)
        self.skipRightBtn.setEnabled(False)
        self.skipLeftBtn.setEnabled(False)
        self.disableAnnotationTools()

    @Slot(QGraphicsSceneMouseEvent)
    def mousePressWhenDrawing(self, event):
        """
        Called when mouse press event is caught in scene during drawing procedure.
        :type event: PySide.QtGui.QGraphicsSceneMouseEvent
        """
        if self.am_I_Drawing:
            point = event.scenePos()
            self.drawing_class.draw(point, self.zoom)

    @Slot(QGraphicsSceneMouseEvent)
    def mouseMoveEventInScene(self, event):
        """
        Called when mouse move event is caught in scene during drawing procedure.
        :type event: PySide.QtGui.QGraphicsSceneMouseEvent
        """
        if self.am_I_Drawing:
            point = event.scenePos()
            self.drawing_class.draw(point, self.zoom)

    @Slot(QGraphicsSceneMouseEvent)
    def mouseReleaseEventInScene(self, event):
        """
        Called when mouse release event is caught in scene during drawing procedure.
        :type event: PySide.QtGui.QGraphicsSceneMouseEvent
        """
        if self.am_I_Drawing:
            point = event.scenePos()
            self.drawing_class.draw(point, self.zoom, last_drawing=True)
            self.endDrawing(cancel=False)

    @Slot()
    def displayKeyboardShortcutsDialog(self):
        """
        Pops-up shortcuts dialog with author and version information
        """
        pathToHtml = os.path.join(self.rootPath, 'data', 'text', 'gui_keys.en.html')

        try:
            with open(pathToHtml) as f:
                shortcutsData = f.read()

        except IOError:
            logger.exception("Error when loading keyboard shortcuts file.")
            QApplication.beep()
            models.repository.logs.insert('gui.exception.shortcuts_file_error',
                                          "Error when loading keyboard shortcuts file.",
                                          annotator_id=self.user.id)
            return

        shortcutsDialog = QMessageBox()
        shortcutsDialog.setText(shortcutsData)
        shortcutsDialog.setTextFormat(Qt.RichText)
        shortcutsDialog.setWindowIcon(self.windowIcon())

        # parse html title from html
        htmlDataL = shortcutsData.lower()
        begin = htmlDataL.find('<title>')
        end = htmlDataL.find('</title>')
        if begin != -1 and end != -1:
            title = shortcutsData[begin+len('<title>'):end].strip()
        else:
            logger.warning("Unable to parse <title> from html shortcuts file")
            title = "Tovian - Keyboard shortcuts"
        shortcutsDialog.setWindowTitle(title)
        shortcutsDialog.exec_()

    @Slot()
    def displayAboutDialog(self):
        """
        Pops-up about dialog with author and version information
        """
        pathToHtml = os.path.join(self.rootPath, 'data', 'text', 'gui_about.en.html')
        pathToVersionFile = os.path.join(self.rootPath, 'data', 'version.json')

        try:
            with open(pathToHtml) as f:
                htmlData = f.read()

            with open(pathToVersionFile) as f:
                versionData = json.loads(f.read())
        except IOError:
            logger.exception("Error when loading about files")
            QApplication.beep()
            models.repository.logs.insert('gui.exception.about_dialog_files_error',
                                          "Error when loading about files",
                                          annotator_id=self.user.id)
            return

        aboutDialog = QMessageBox()
        aboutDialog.setText(htmlData % versionData)
        aboutDialog.setTextFormat(Qt.RichText)
        aboutDialog.setWindowIcon(self.windowIcon())

        # parse html title from html
        htmlDataL = htmlData.lower()
        begin = htmlDataL.find('<title>')
        end = htmlDataL.find('</title>')
        if begin != -1 and end != -1:
            title = htmlData[begin+len('<title>'):end].strip()
        else:
            logger.warning("Unable to parse <title> from html about file")
            title = "Tovian - About"
        aboutDialog.setWindowTitle(title)
        aboutDialog.exec_()

    @Slot()
    def displayGoToDialog(self):
        """
        Opens goto dialog as modal
        """
        gotoDialog = goto.GoToDialog(self.fps, self.frame_count, self.video_duration, self.memorized_pos, self)
        gotoDialog.setWindowFlags(gotoDialog.windowFlags() ^ Qt.WindowContextHelpButtonHint)

        gotoDialog.newTimeSelected.connect(self.player.seek)
        gotoDialog.newTimeSelected.connect(self.player.resetPerFrameSlider)

        gotoDialog.exec_()

    @Slot()
    def displayBufferingMsg(self):
        """
        When buffer starts loading from database, signal is emitted and the message is displayed.
        """
        self.statusbar.showMessage(self.buffering_msg)

    @Slot()
    def memoryCurrentPos(self):
        """
        Memorizes current frame number and video time.
        """
        logger.debug("Memorizing current video position")
        self.memorized_pos = (self.player.getCurrentFrame(), self.player.currentTime()/1000.0)
        self.statusbar.showMessage(self.position_memorized_msg, self.SHORT_MSG_DURATION)
