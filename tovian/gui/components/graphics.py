# -*- coding: utf-8 -*-

"""
Graphics components:
- Annotation tools - rectangle, circle, point
- Graphics scene
- Drawing class
"""

__version__ = "$Id: graphics.py 348 2013-12-12 11:40:55Z herbig $"

import math
from operator import itemgetter

from PySide.QtCore import *
from PySide.QtGui import *

from tovian.models.entity import default_options


class AnnotationBaseClass(QAbstractGraphicsShapeItem):
    """
    Base class of custom QGraphicsItem, which can be resized and moved.
    """

    MIN_WIDTH = 2.0
    MIN_HEIGHT = 2.0
    DEFAULT_GRIP_SIZE = 6.0
    DEFAULT_BORDER = 2.0
    DEFAULT_FONT_SIZE = 10

    default_colors = default_options['gui']['color']
    normal_color = default_colors['annotation_object_visual']
    selected_color = default_colors['annotation_object_visual_focus']
    not_active_color = default_colors['annotation_object_visual_edit']

    is_active_in_frame = True
    selected_grip = None
    is_grip_selected = False
    is_item_hovered = False
    grips_are_initialized = False
    grip_size = 6                  # anchor rectangle size in px
    border = 2

    # TODO FUTURE - refactor grips as children
    top_left_grip = None
    top_right_grip = None
    bottom_left_grip = None
    bottom_right_grip = None
    left_side_grip = None
    right_side_grip = None
    top_grip = None
    bottom_grip = None

    def __init__(self, x, y, width, height, scene, color, text, font_size):
        """
        Constructs custom QGraphicsItem rectangle. Sets its position, dimension and the scene.
        :param x: X coordinate
        :param y: Y coordinate
        :param width: inner width
        :param height: inner height
        :param scene: parent scene
        :param color: dictionary with preferred colors for current object
        :param text: Global and local text to display
        :type x: float
        :type y: float
        :type width: float
        :type height: float
        :type scene: GraphicsScene
        :type color: dict
        :type text: tuple of unicode
        """
        super(AnnotationBaseClass, self).__init__()
        self.scene = scene              # parent scene reference

        # Global and Local label
        global_text, local_text = text
        self.global_text_item = QGraphicsSimpleTextItem(global_text, self)
        self.local_text_item = QGraphicsSimpleTextItem(local_text, self)
        self.global_text_item.setFlag(QGraphicsItem.ItemIgnoresTransformations)
        self.local_text_item.setFlag(QGraphicsItem.ItemIgnoresTransformations)
        if font_size:
            self.setFontSize(font_size)

        if color:
            self.normal_color = color['annotation_object_visual']
            self.selected_color = color['annotation_object_visual_focus']
            self.not_active_color = color['annotation_object_visual_edit']

        # set dimensions and position
        self.setPos(QPointF(x, y))
        self._updateRelPos()            # needs to be updated manually for the first time
        self.resize(width, height)

        # setup
        pen = QPen(QColor(self.normal_color))
        pen.setWidthF(self.border)
        self.setPen(pen)
        self.setAcceptHoverEvents(True)                             # mouse hover events can be accepted
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemSendsGeometryChanges)
        self._updateCoordinates()                                   # recalculate coordinates from given dimensions

        self.scene.viewResized.connect(self.updatePosInView)

        self.global_text_item.setBrush(QBrush(self.pen().color()))
        self.local_text_item.setBrush(QBrush(self.pen().color()))

    def itemChange(self, change, new_value):
        """
        Method automatically called when item's state changed.
        :param change: type of change
        :type change: PySide.QtGui.QGraphicsItem.GraphicsItemChange
        :param new_value: new value
        :return: changed object
        :rtype: object
        """
        # position changed
        if change == QGraphicsItem.ItemPositionHasChanged and not self.is_grip_selected:
            self._updateRelPos(new_value)       # update proportional position
            self.scene.geometryChanged.emit(self, new_value)

        return QGraphicsItem.itemChange(self, change, new_value)

    def pos(self, relative=False):
        """
        Returns current absolute or relative position.
        :type relative: bool
        :rtype: PySide.QtCore.QPointF
        """
        if relative:
            return QPointF(self.x_prop, self.y_prop)
        else:
            return super(AnnotationBaseClass, self).pos()

    def pos_(self, relative=False):
        """
        Return position of top left and bottom right corner
        :type relative: bool
        :rtype: tuple of int
        """
        x = self.x()
        y = self.y()
        x1 = x + self.item_x1
        x2 = x + self.item_x2
        y1 = y + self.item_y1
        y2 = y + self.item_y2

        if relative:
            video_size = self.scene.getVideoSize()
            view_width = float(video_size.width())
            view_height = float(video_size.height())
            x1 /= view_width
            x2 /= view_width
            y1 /= view_height
            y2 /= view_height
            return x1, y1, x2, y2
        else:
            return x1, y1, x2, y2

    def setPos(self, pos, relative=False):
        """
        Set new absolute or relative position.
        :type pos: PySide.QtCore.QPointF
        :type relative: bool
        """
        if relative:
            video_size = self.scene.getVideoSize()
            view_width = video_size.width()
            view_height = video_size.height()
            super(AnnotationBaseClass, self).setPos(pos.x() * view_width, pos.y() * view_height)
        else:
            super(AnnotationBaseClass, self).setPos(pos.x(), pos.y())

    def updatePosInView(self):
        """
        Called when QGraphicsView is resized to preserve relative position of the item.
        """
        rel_size = self.size(relative=True)
        self.resize(rel_size.width(), rel_size.height(), relative=True)
        self.setPos(self.pos(relative=True), relative=True)

    def resize(self, width, height, relative=False):
        """
        Resizes item to new width and height.
        :type width: float
        :type height: float
        :type relative: bool
        """
        # video widget size
        video_size = self.scene.getVideoSize()
        view_width = video_size.width()
        view_height = video_size.height()

        self.prepareGeometryChange()

        if relative:
            new_absolute_width = width * float(view_width)
            new_absolute_height = height * float(view_height)
            self.width = new_absolute_width if new_absolute_width >= self.MIN_WIDTH else self.MIN_WIDTH
            self.height = new_absolute_height if new_absolute_height >= self.MIN_HEIGHT else self.MIN_HEIGHT
            self.width_rel = width if new_absolute_width >= self.MIN_WIDTH else self.MIN_WIDTH / float(view_width)
            self.height_rel = height if new_absolute_height >= self.MIN_HEIGHT else self.MIN_HEIGHT / float(view_height)
        else:
            self.width = width if width >= self.MIN_WIDTH else self.MIN_WIDTH
            self.height = height if height >= self.MIN_HEIGHT else self.MIN_HEIGHT
            self.width_rel = self.width / float(view_width)
            self.height_rel = self.height / float(view_height)

        self._updateCoordinates()
        self.update()

    def size(self, relative=False):
        """
        Returns absolute or relative size of the object.
        :rtype : PySide.QtCore.QSizeF
        :type relative: bool
        """
        if relative:
            return QSizeF(self.width_rel, self.height_rel)
        else:
            return QSizeF(self.width, self.height)

    def _updateRelPos(self, new_absolute=None):
        """
        Called when absolute position changed to update the relative values.
        :type new_absolute: PySide.QtCore.QPointF
        """
        video_size = self.scene.getVideoSize()
        view_width = float(video_size.width())
        view_height = float(video_size.height())

        if new_absolute:
            self.x_prop = new_absolute.x() / view_width
            self.y_prop = new_absolute.y() / view_height
        else:
            self.x_prop = self.x() / view_width
            self.y_prop = self.y() / view_height

    def _updateCoordinates(self):
        """
        Method updates coordinates which holds topL and botR corner position
        """
        self.item_x1 = 0 - self.width / 2.0
        self.item_y1 = 0 - self.height / 2.0
        self.item_x2 = 0 + self.width / 2.0
        self.item_y2 = 0 + self.height / 2.0

        self._updateLabelPos()

    def _updateLabelPos(self):
        """
        Called to update global and local label position when item's zoom or position changed.
        """
        y_scale = self.scene.view.transform().m22()
        self.global_text_item.setPos(self.item_x1, self.item_y1 - self.global_text_item.boundingRect().height() / y_scale)
        self.local_text_item.setPos(self.item_x1, self.item_y2 + 2 / y_scale)

    def updateAfterScale(self, scale):
        """
        Called when scene is zoomed to recalculate item's border, grip size a label positions
        :type scale: float
        """
        pen = self.pen()
        self.border = self.DEFAULT_BORDER / scale
        pen.setWidthF(self.border)
        self.setPen(pen)
        self.grip_size = self.DEFAULT_GRIP_SIZE / scale
        self._updateLabelPos()

    def _whichGripIsSelected(self, cursor_position):
        """
        Determines whether the cursor position is inside the grip.
        :param cursor_position: Position of cursor (point)
        :type cursor_position: PySide.QtCore.QPointF
        :return: dictionary ('position': str, 'object': QRectF) or None
        :rtype : dict or None
        """

        if not self.grips_are_initialized:
            return None

        if self.top_left_grip.contains(cursor_position):
            return {'position': "TL", 'object': self.top_left_grip}
        elif self.top_right_grip.contains(cursor_position):
            return {'position': "TR", 'object': self.top_right_grip}
        elif self.bottom_left_grip.contains(cursor_position):
            return {'position': "BL", 'object': self.bottom_left_grip}
        elif self.bottom_right_grip.contains(cursor_position):
            return {'position': "BR", 'object': self.bottom_right_grip}
        elif self.left_side_grip.contains(cursor_position):
            return {'position': "L", 'object': self.left_side_grip}
        elif self.right_side_grip.contains(cursor_position):
            return {'position': "R", 'object': self.right_side_grip}
        elif self.top_grip.contains(cursor_position):
            return {'position': "T", 'object': self.top_grip}
        elif self.bottom_grip.contains(cursor_position):
            return {'position': "B", 'object': self.bottom_grip}
        else:
            return None

    def _resizeByMouse(self, cursor_pos_in_rect):
        """
        Resizes object depending on the cursor position and selected anchor.
        :param cursor_pos_in_rect: cursor position in rect coordinates
        :type cursor_pos_in_rect: PySide.QtCore.QPointF
        :rtype : None
        """
        cursor_pos_in_scene = self.mapToScene(cursor_pos_in_rect)
        anchor_position = self.selected_grip['position']
        self.prepareGeometryChange()        # needed to tell Qt or python crashes

        # sets center of object so that the opposite corner stayed fixed
        if anchor_position == "TL":
            fixed_point_x, fixed_point_y = self.x() + self.width / 2.0, self.y() + self.height / 2.0
            new_width = (fixed_point_x - cursor_pos_in_scene.x())
            new_height = (fixed_point_y - cursor_pos_in_scene.y())
            self.width = new_width if new_width > self.MIN_WIDTH else self.MIN_WIDTH
            self.height = new_height if new_height > self.MIN_HEIGHT else self.MIN_HEIGHT
            self.setX(fixed_point_x - self.width / 2.0)
            self.setY(fixed_point_y - self.height / 2.0)
        elif anchor_position == "TR":
            fixed_point_x, fixed_point_y = self.x() - self.width / 2.0, self.y() + self.height / 2.0
            new_width = -(fixed_point_x - cursor_pos_in_scene.x())
            new_height = (fixed_point_y - cursor_pos_in_scene.y())
            self.width = new_width if new_width > self.MIN_WIDTH else self.MIN_WIDTH
            self.height = new_height if new_height > self.MIN_HEIGHT else self.MIN_HEIGHT
            self.setX(fixed_point_x + self.width / 2.0)
            self.setY(fixed_point_y - self.height / 2.0)
        elif anchor_position == "BR":
            fixed_point_x, fixed_point_y = self.x() - self.width / 2.0, self.y() - self.height / 2.0
            new_width = -(fixed_point_x - cursor_pos_in_scene.x())
            new_height = -(fixed_point_y - cursor_pos_in_scene.y())
            self.width = new_width if new_width > self.MIN_WIDTH else self.MIN_WIDTH
            self.height = new_height if new_height > self.MIN_HEIGHT else self.MIN_HEIGHT
            self.setX(fixed_point_x + self.width / 2.0)
            self.setY(fixed_point_y + self.height / 2.0)
        elif anchor_position == "BL":
            fixed_point_x, fixed_point_y = self.x() + self.width / 2.0, self.y() - self.height / 2.0
            new_width = (fixed_point_x - cursor_pos_in_scene.x())
            new_height = -(fixed_point_y - cursor_pos_in_scene.y())
            self.width = new_width if new_width > self.MIN_WIDTH else self.MIN_WIDTH
            self.height = new_height if new_height > self.MIN_HEIGHT else self.MIN_HEIGHT
            self.setX(fixed_point_x - self.width / 2.0)
            self.setY(fixed_point_y + self.height / 2.0)
        elif anchor_position == "T":
            fixed_point_x, fixed_point_y = self.x() + self.width / 2.0, self.y() + self.height / 2.0
            new_height = (fixed_point_y - cursor_pos_in_scene.y())
            self.height = new_height if new_height > self.MIN_HEIGHT else self.MIN_HEIGHT
            self.setX(fixed_point_x - self.width / 2.0)
            self.setY(fixed_point_y - self.height / 2.0)
        elif anchor_position == "R":
            fixed_point_x, fixed_point_y = self.x() - self.width / 2.0, self.y() - self.height / 2.0
            new_width = -(fixed_point_x - cursor_pos_in_scene.x())
            self.width = new_width if new_width > self.MIN_WIDTH else self.MIN_WIDTH
            self.setX(fixed_point_x + self.width / 2.0)
            self.setY(fixed_point_y + self.height / 2.0)
        elif anchor_position == "B":
            fixed_point_x, fixed_point_y = self.x() - self.width / 2.0, self.y() - self.height / 2.0
            new_height = -(fixed_point_y - cursor_pos_in_scene.y())
            self.height = new_height if new_height > self.MIN_HEIGHT else self.MIN_HEIGHT
            self.setX(fixed_point_x + self.width / 2.0)
            self.setY(fixed_point_y + self.height / 2.0)
        elif anchor_position == "L":
            fixed_point_x, fixed_point_y = self.x() + self.width / 2.0, self.y() + self.height / 2.0
            new_width = (fixed_point_x - cursor_pos_in_scene.x())
            self.width = new_width if new_width > self.MIN_WIDTH else self.MIN_WIDTH
            self.setX(fixed_point_x - self.width / 2.0)
            self.setY(fixed_point_y - self.height / 2.0)

        # dimensions has been changed so object's corners must be recalculated
        video_size = self.scene.getVideoSize()
        view_width = float(video_size.width())
        view_height = float(video_size.height())

        self.x_prop = self.x() / view_width
        self.y_prop = self.y() / view_height
        self.width_rel = self.width / float(view_width)
        self.height_rel = self.height / float(view_height)
        self._updateCoordinates()

        self.scene.geometryChanged.emit(self, self.pos())

    def setId(self, user_id):
        """
        Set user object as id
        :param user_id: object identification
        :type user_id: object
        """
        self.setData(0, user_id)

    def getId(self):
        """
        Returns user object id
        """
        return self.data(0)

    def setFontSize(self, pixel):
        """
        Changes font size of global and local text.
        :param pixel: font size in px
        :type pixel: int
        """
        if not pixel:
            return

        font = self.global_text_item.font()
        font.setPixelSize(pixel)
        self.global_text_item.setFont(font)
        self.local_text_item.setFont(font)

    def setLabels(self, global_text=None, local_text=None):
        """
        Sets global and local item label.
        :type global_text: unicode
        :type local_text: unicode
        :raise AttributeError: When both local and global text is None.
        """
        if global_text is None and local_text is None:
            raise AttributeError("Both attributes cannot be None!")

        if global_text is not None:
            self.global_text_item.setText(global_text)

        if local_text is not None:
            self.local_text_item.setText(local_text)

    def drawDotted(self):
        """
        Draws object with dotted line
        """
        pen = self.pen()
        pen.setStyle(Qt.DotLine)
        self.setPen(pen)

    def drawSolid(self):
        """
        Draws object with solid line (default)
        """
        pen = self.pen()
        pen.setStyle(Qt.SolidLine)
        self.setPen(pen)

    def markAsSelected(self):
        """
        When object is selected, object is marked with specified color
        """
        pen = self.pen()
        color = QColor(self.selected_color)
        pen.setColor(color)
        self.setPen(pen)
        self.global_text_item.setBrush(QBrush(color))
        self.local_text_item.setBrush(QBrush(color))

    def markAsNotActive(self):
        """
        When object is edited, object is marked with specified color
        """
        pen = self.pen()
        color = QColor(self.not_active_color)
        pen.setColor(color)
        self.setPen(pen)
        self.global_text_item.setBrush(QBrush(color))
        self.local_text_item.setBrush(QBrush(color))

    def markAsDefault(self):
        """
        Default object is marked with default color
        """
        pen = self.pen()
        color = QColor(self.normal_color)
        pen.setColor(color)
        self.setPen(pen)
        self.global_text_item.setBrush(QBrush(color))
        self.local_text_item.setBrush(QBrush(color))

    def setActiveInFrame(self, state):
        """
        Set object as edited
        :type state: bool
        """
        self.is_active_in_frame = state

    def activeInFrame(self):
        """
        Returns if object is currently edited
        :rtype: bool
        """
        return self.is_active_in_frame

    def mouseMoveEvent(self, event):
        """
        Implemented virtual function to catch and process mouse movement.
        :param event: Event object given by Qt
        :type event: PySide.QtGui.QGraphicsSceneMouseEvent
        """

        if self.is_grip_selected:
            self._resizeByMouse(event.pos())
            pass
        else:
            super(AnnotationBaseClass, self).mouseMoveEvent(event)

    def mousePressEvent(self, event):
        """
        Implemented virtual function to catch and process mouse press event
        When left button is pressed inside some grip, it starts mouse resizing procedure.
        :type event: PySide.QtGui.QGraphicsSceneMouseEvent
        """
        if event.button() is Qt.LeftButton:
            self.scene.clearSelection()
            self.setSelected(True)

            # if some grip is clicked, enable item resize
            self.selected_grip = self._whichGripIsSelected(event.pos())
            if self.selected_grip:
                self.is_grip_selected = True
                # remembers old values to calculate new ones (difference between this position and new after mouse movement)
                self.old_width = self.width
                self.old_height = self.height
                self.old_scene_cursor_pos = self.mapToScene(event.pos())
                # resize item as mouse cursor moves
                #self._resizeByMouse(event.pos())
            else:
                self.is_grip_selected = False
                self.selected_grip = None
                super(AnnotationBaseClass, self).mousePressEvent(event)     # call parent so object can be moved (movable)
        elif not self.is_grip_selected:
            super(AnnotationBaseClass, self).mousePressEvent(event)     # call parent so object can be moved (movable)

    def mouseReleaseEvent(self, event):
        """
        Implemented virtual function of mouse button release.
        When left button is released, it ends mouse resizing procedure.
        :type event: PySide.QtGui.QGraphicsSceneMouseEvent
        """

        if event.button() is Qt.LeftButton:
            if self.is_grip_selected:
                self.is_grip_selected = False
                self.selected_grip = None
            else:
                super(AnnotationBaseClass, self).mouseReleaseEvent(event)
        elif not self.is_grip_selected:
            super(AnnotationBaseClass, self).mouseReleaseEvent(event)

    def hoverEnterEvent(self, event):
        """
        Implemented virtual function of mouse hover when entering the object.
        When user hovers, it renders item's grips.
        :type event: PySide.QtGui.QGraphicsSceneHoverEvent
        """

        super(AnnotationBaseClass, self).hoverEnterEvent(event)
        self.is_item_hovered = True
        self.update()

    def hoverMoveEvent(self, event):
        """
        Implemented virtual function of mouse hover when moving in the object.
        Changes cursor depending on cursor position (grip) to resizing arrows.
        :type event: PySide.QtGui.QGraphicsSceneHoverEvent
        """
        super(AnnotationBaseClass, self).hoverMoveEvent(event)

        if self.isSelected():
            hovered_object = self._whichGripIsSelected(event.pos())
            if not hovered_object:
                self.setCursor(Qt.SizeAllCursor)
            else:
                hovered_object = hovered_object['position']
                if hovered_object == "TL" or hovered_object == "BR":
                    self.setCursor(Qt.SizeFDiagCursor)
                elif hovered_object == "TR" or hovered_object == "BL":
                    self.setCursor(Qt.SizeBDiagCursor)
                elif hovered_object == "T" or hovered_object == "B":
                    self.setCursor(Qt.SizeVerCursor)
                elif hovered_object == "L" or hovered_object == "R":
                    self.setCursor(Qt.SizeHorCursor)

    def hoverLeaveEvent(self, event):
        """
        Implemented virtual function of mouse hover when leaving the object.
        When user hovers out, it hides item's grips.
        :type event: PySide.QtGui.QGraphicsSceneHoverEvent
        """
        super(AnnotationBaseClass, self).hoverLeaveEvent(event)
        self.is_item_hovered = False
        self.update()


class AnnotationRect(AnnotationBaseClass):
    """
    Custom QGraphicsItem rectangle, which can be resized and moved.
    """

    def __init__(self, x, y, width, height, scene, color=None,
                 text=('', ''), font_size=AnnotationBaseClass.DEFAULT_FONT_SIZE):
        """
        Constructs custom QGraphicsItem rectangle. Sets its position, dimensions, ID and scene.
        :param x: X coordinate
        :param y: Y coordinate
        :param width: inner width
        :param height: inner height
        :param scene: parent scene
        :param color: dictionary with preferred colors for current object
        :param text: Global and local text label
        :type x: float
        :type y: float
        :type width: float
        :type height: float
        :type scene: PySide.QtGui.QGraphicsScene
        :type color: dict
        :type text: tuple of unicode
        """
        super(AnnotationRect, self).__init__(x, y, width, height, scene, color, text, font_size)

    def boundingRect(self):
        """
        Computes and sets item's bounding rectangle, so Qt knows where to render.
        If bounding rect is not set correctly, artifacts may shows up !!!
        This is REQUIRED class method by Qt!
        :return: Bounding rectangle
        :rtype: PySide.QtCore.QRectF
        """
        self.border = self.grip_size / 2.0 + self.pen().width() + 1
        return QRectF(self.item_x1 - self.border / 2.0, self.item_y1 - self.border / 2.0,
                      self.width + self.border, self.height + self.border)

    def paint(self, painter, option, widget):
        """
        When update() called, method paints objects on widget (item).
        :type painter: PySide.QtGui.QPainter
        :type option: PySide.QtGui.QStyleOptionGraphicsItem
        :type widget: PySide.QtGui.QWidget
        """
        # sets items default values
        pen = self.pen()
        pen.setJoinStyle(Qt.MiterJoin)
        painter.setPen(pen)
        painter.setBrush(self.brush())
        painter.setRenderHint(QPainter.Antialiasing)
        self.border = self.grip_size / 2.0 + self.pen().width()    # item's max border

        # paint main rectangle
        painter.drawRect(QRectF(self.item_x1, self.item_y1, self.width, self.height))

        if self.is_item_hovered and self.isSelected():
            anchor_half = self.grip_size / 2.0
            # rect corner and side anchors
            self.top_left_grip = QRectF(self.item_x1 - anchor_half, self.item_y1 - anchor_half, self.grip_size, self.grip_size)
            self.top_right_grip = QRectF(self.item_x2 - anchor_half, self.item_y1 - anchor_half, self.grip_size, self.grip_size)
            self.bottom_left_grip = QRectF(self.item_x1 - anchor_half, self.item_y2 - anchor_half, self.grip_size, self.grip_size)
            self.bottom_right_grip = QRectF(self.item_x2 - anchor_half, self.item_y2 - anchor_half, self.grip_size, self.grip_size)
            self.left_side_grip = QRectF(self.item_x1 - anchor_half, 0 - anchor_half, self.grip_size, self.grip_size)
            self.right_side_grip = QRectF(self.item_x2 - anchor_half, 0 - anchor_half, self.grip_size, self.grip_size)
            self.top_grip = QRectF(0 - anchor_half, self.item_y1 - anchor_half, self.grip_size, self.grip_size)
            self.bottom_grip = QRectF(0 - anchor_half, self.item_y2 - anchor_half, self.grip_size, self.grip_size)

            # paint anchor rectangles
            painter.setBrush(Qt.black)
            painter.setPen(QPen(self.brush(), 0))
            painter.drawRect(self.top_left_grip)
            painter.drawRect(self.top_right_grip)
            painter.drawRect(self.bottom_left_grip)
            painter.drawRect(self.bottom_right_grip)
            painter.drawRect(self.left_side_grip)
            painter.drawRect(self.right_side_grip)
            painter.drawRect(self.top_grip)
            painter.drawRect(self.bottom_grip)
            # center of the rect

            painter.drawRect(QRectF(0 - anchor_half, 0 - anchor_half, self.grip_size, self.grip_size))
            self.grips_are_initialized = True

    def getOriginalPosInVideo(self, x, y, orig_width, orig_height):
        """
        Return scaled value of x1, y1, x2, y2 to video width/height original size
        :param x: current x
        :param y: current y
        :param orig_width: original video width
        :param orig_height: original video height
        :return: (x1, y1, x2, y2)
        :rtype: tuple of int
        """
        video_size = self.scene.getVideoSize()
        view_width = video_size.width()
        view_height = video_size.height()

        orig_x1 = round(((x - self.width/2.0) / float(view_width)) * orig_width)
        orig_y1 = round(((y - self.height/2.0) / float(view_height)) * orig_height)
        orig_x2 = round(((x + self.width/2.0) / float(view_width)) * orig_width)
        orig_y2 = round(((y + self.height/2.0) / float(view_height)) * orig_height)

        return orig_x1, orig_y1, orig_x2, orig_y2


class AnnotationCircle(AnnotationBaseClass):
    """
    Custom QGraphicsItem circle, which can be resized and moved.
    """

    def __init__(self, x, y, width, scene, color=None,
                 text=('', ''), font_size=AnnotationBaseClass.DEFAULT_FONT_SIZE):
        """
        Constructs custom QGraphicsItem rectangle. Sets its position, dimensions, ID, parent and scene.
        :param x: X coordinate
        :param y: Y coordinate
        :param width: inner width
        :param scene: parent scene
        :param color: dictionary with preferred colors for current object
        :param text: Global and local text label
        :type x: float
        :type y: float
        :type width: int
        :type scene: PySide.QtGui.QGraphicsScene
        :type color: dict
        :type text: tuple of unicode
        """
        super(AnnotationCircle, self).__init__(x, y, width, width, scene, color, text, font_size)

    def boundingRect(self):
        """
        Computes and sets item's bounding rectangle, so Qt knows where to render.
        If bounding rect is not set correctly, artifacts may shows up !!!
        This is REQUIRED class method by Qt!
        :return: Bounding rectangle
        :rtype: PySide.QtCore.QRectF
        """
        self.border = self.grip_size / 2.0 + self.pen().width() + 1
        return QRectF(self.item_x1 - self.border / 2.0, self.item_y1 - self.border / 2.0,
                      self.width + self.border, self.width + self.border)

    def paint(self, painter, option, widget):
        """
        When update() called, method paints objects on widget (item).
        :type painter: PySide.QtGui.QPainter
        :type option: PySide.QtGui.QStyleOptionGraphicsItem
        :type widget: PySide.QtGui.QWidget
        """
        # sets items default values
        pen = self.pen()
        pen.setJoinStyle(Qt.MiterJoin)
        painter.setPen(pen)
        painter.setBrush(self.brush())
        painter.setRenderHint(QPainter.Antialiasing)

        # paint main rectangle
        painter.drawEllipse(QRectF(0 - self.width/2.0, 0 - self.width/2.0, self.width, self.width))

        if self.is_item_hovered and self.isSelected():
            anchor_half = self.grip_size / 2.0
            # rect corner and side anchors
            self.top_left_grip = QRectF(self.item_x1 - anchor_half, self.item_y1 - anchor_half, self.grip_size, self.grip_size)
            self.top_right_grip = QRectF(self.item_x2 - anchor_half, self.item_y1 - anchor_half, self.grip_size, self.grip_size)
            self.bottom_left_grip = QRectF(self.item_x1 - anchor_half, self.item_y2 - anchor_half, self.grip_size, self.grip_size)
            self.bottom_right_grip = QRectF(self.item_x2 - anchor_half, self.item_y2 - anchor_half, self.grip_size, self.grip_size)

            # paint anchor rectangles
            painter.setBrush(Qt.black)
            painter.setPen(QPen(self.brush(), 0))
            painter.drawRect(self.top_left_grip)
            painter.drawRect(self.top_right_grip)
            painter.drawRect(self.bottom_left_grip)
            painter.drawRect(self.bottom_right_grip)
            # center of the rect
            painter.drawRect(QRectF(0 - anchor_half, 0 - anchor_half, self.grip_size, self.grip_size))

            self.grips_are_initialized = True

    def _updateCoordinates(self):
        """
        Method updates coordinates which holds topL and botR corner position
        """
        self.item_x1 = 0 - self.width / 2.0
        self.item_y1 = 0 - self.width / 2.0
        self.item_x2 = 0 + self.width / 2.0
        self.item_y2 = 0 + self.width / 2.0

        self.global_text_item.setPos(self.item_x1, self.item_y1 - self.global_text_item.boundingRect().height())
        self.local_text_item.setPos(self.item_x1, self.item_y2)

    def _whichGripIsSelected(self, cursor_position):
        """
        Determines whether the cursor position is inside anchor.
        Method should not be accessed from outside. Depends on current class state!
        :param cursor_position: Position of cursor (point)
        :type cursor_position: PySide.QtCore.QPointF
        :return: dictionary ('position': str, 'object': QRectF) or None
        :rtype : dict or None
        """
        if not self.grips_are_initialized:
            return None

        if self.top_left_grip.contains(cursor_position):
            return {'position': "TL", 'object': self.top_left_grip}
        elif self.top_right_grip.contains(cursor_position):
            return {'position': "TR", 'object': self.top_right_grip}
        elif self.bottom_left_grip.contains(cursor_position):
            return {'position': "BL", 'object': self.bottom_left_grip}
        elif self.bottom_right_grip.contains(cursor_position):
            return {'position': "BR", 'object': self.bottom_right_grip}
        else:
            return None

    def _resizeByMouse(self, cursor_pos_in_rect):
        """
        Resizes object depending on the cursor position and selected anchor.
        Method should not be accessed from outside. Depends on current class state!
        :param cursor_pos_in_rect: Cursor position mapped to object's coordinate system
        :type cursor_pos_in_rect: PySide.QtCore.QPointF
        """
        self.prepareGeometryChange()

        # calculates the Euclidean distance between the center and the mouse cursor
        radius = math.sqrt(((0 - cursor_pos_in_rect.x()) ** 2 + (0 - cursor_pos_in_rect.y()) ** 2) / 2.0)
        self.width = 2 * radius

        video_size = self.scene.getVideoSize()
        view_width = float(video_size.width())
        view_height = float(video_size.height())

        self.x_prop = self.x() / view_width
        self.y_prop = self.y() / view_height
        self.width_rel = self.width / float(view_width)
        self.height_rel = self.height / float(view_height)
        self._updateCoordinates()

        self.scene.geometryChanged.emit(self, self.pos())

    def getOriginalPosInVideo(self, x, y, orig_width, orig_height):
        """
        Return scaled value of x1, y1, x2, y2 to video width/height original size
        :param x: current x
        :param y: current y
        :param orig_width: original video width
        :param orig_height: original video height
        :return: (x1, y1, x2, y2)
        :rtype: tuple of int
        """
        video_size = self.scene.getVideoSize()
        view_width = video_size.width()
        view_height = video_size.height()

        orig_x = round((x / float(view_width)) * orig_width)
        orig_y = round((y / float(view_height)) * orig_height)
        orig_r = round((self.width / float(view_width)) * orig_width) / 2.0

        return orig_x, orig_y, orig_r


class AnnotationPoint(AnnotationBaseClass):
    """
    Custom QGraphicsItem point, which can be and moved.
    """

    grip_size = 0     # overridden base anchor size <= Point has no anchors
    DEFAULT_WIDTH = 0.025

    def __init__(self, x, y, scene, color=None,
                 text=('', ''), font_size=AnnotationBaseClass.DEFAULT_FONT_SIZE):
        """
        Constructs custom QGraphicsItem rectangle. Sets its position, dimensions, ID, parent and scene.
        :param x: X coordinate
        :param y: Y coordinate
        :param scene: parent scene
        :param color: dictionary with preferred colors for current object
        :param text: Global and local text to display
        :type x: float
        :type y: float
        :type scene: PySide.QtGui.QGraphicsScene
        :type color: dict
        :type text: tuple of unicode
        """
        super(AnnotationPoint, self).__init__(x, y, self.MIN_WIDTH, self.MIN_WIDTH, scene, color, text, font_size)

        pen = self.pen()
        pen.setJoinStyle(Qt.MiterJoin)
        self.setPen(pen)

        self.resize(self.DEFAULT_WIDTH, relative=True)      # choose right relative size

        # object is not resizable by mouse
        self.selected_grip = None
        self.is_grip_selected = False

    def boundingRect(self):
        """
        Computes and sets item's bounding rectangle, so Qt knows where to render.
        If bounding rect is not set correctly, artifacts may shows up !!!
        This is REQUIRED class method by Qt!
        :return: Bounding rectangle
        :rtype: PySide.QtCore.QRectF
        """
        return QRectF(self.item_x1 - self.border / 2.0, self.item_y1 - self.border / 2.0,
                      self.width + self.border, self.height + self.border)

    def paint(self, painter, option, widget):
        """
        When update() called, method paints objects on widget (item).
        :type painter: PySide.QtGui.QPainter
        :type option: PySide.QtGui.QStyleOptionGraphicsItem
        :type widget: PySide.QtGui.QWidget
        """
        # sets items default values
        painter.setPen(self.pen())
        painter.setBrush(self.brush())
        painter.setRenderHint(QPainter.Antialiasing)

        # paint surrounding circle
        if self.is_item_hovered or self.isSelected():
            painter.drawEllipse(QRectF(self.item_x1, self.item_y1, self.width, self.height))

        # PAINT CROSS
        pen = self.pen()
        pen.setStyle(Qt.SolidLine)      # always set solid line for cross
        painter.setPen(pen)
        painter.drawLine(0, 0 - self.width/4.0, 0, self.width/4.0)
        painter.drawLine(0 - self.height/4.0, 0, self.height/4.0, 0)

    def _whichGripIsSelected(self, cursor_position):
        """
        Overridden parent method, no grip can be selected -> returns None
        :type cursor_position: PySide.QtCore.QPointF
        :rtype: None
        """
        return None

    def resize(self, width, height=None, relative=False):
        """
        Resize item to new width. It needs to preserve number of arguments to override parent method.
        Difference between parent method is that parent method calculates relative size from both width and height,
        but point has fixed width = height
        :type width: float
        :type height: None
        :type relative: bool
        """
        # video widget size
        video_size = self.scene.getVideoSize()
        view_width = video_size.width()

        self.prepareGeometryChange()
        if relative:
            newAbsolute = width * float(view_width)
            self.width = newAbsolute if newAbsolute >= self.MIN_WIDTH else self.MIN_WIDTH
            self.height = self.width
            self.width_rel = width if newAbsolute >= self.MIN_WIDTH else (self.MIN_WIDTH / float(view_width))
            self.height_rel = self.width_rel
        else:
            self.width = width if width >= self.MIN_WIDTH else self.MIN_WIDTH
            self.height = self.width
            self.width_rel = self.width / float(view_width)
            self.height_rel = self.width_rel

        self._updateCoordinates()
        self.update()

    def updatePosInView(self):
        """
        Called automatically when QGraphicsView is resized to preserve relative position of the item.
        """
        rel_size = self.size(relative=True)
        self.resize(rel_size.width(), relative=True)
        self.setPos(self.pos(relative=True), relative=True)

    def getOriginalPosInVideo(self, x, y, orig_width, orig_height):
        """
        Return scaled value of x, y to video width/height original size
        :param x: current x
        :param y: current y
        :param orig_width: original video width
        :param orig_height: original video height
        :return: position (x, y)
        :rtype: tuple of int
        """
        # video widget size
        video_size = self.scene.getVideoSize()
        view_width = video_size.width()
        view_height = video_size.height()

        orig_x = round((x / float(view_width)) * orig_width)
        orig_y = round((y / float(view_height)) * orig_height)

        return orig_x, orig_y


class MaskCanvas(QGraphicsPixmapItem):
    """
    Annotation mask canvas, where user can draw the mask with custom opacity in range [1, 255],
    custom brush size and custom brush type.
    """

    RECTANGLE = 0
    CIRCLE = 1

    def __init__(self, image, brush_size=1, opacity=1, brush_type=RECTANGLE, color=(255, 255, 255)):
        """
        :type image: PySide.QtGui.QImage
        :type brush_size: int
        :type opacity: int
        :type color: (int, int, int)
        :raise AttributeError: When opacity is out of range [1, 255].
        """
        if not (1 <= opacity <= 255):
            raise AttributeError("Opacity value is out of range [1, 255]!")

        self.image = image
        self.pixmap = QPixmap.fromImage(image)
        super(MaskCanvas, self).__init__(self.pixmap)

        self.rgb_color = color
        self.brush_opacity = QColor(color[0], color[1], color[2], opacity)
        self.brush_size = int(brush_size)
        self.brush_hsize = self.brush_size / 2.0
        self.brush_type = brush_type

        # setup pen and brush color
        self.painter = QPainter(self.image)
        self.painter.setCompositionMode(QPainter.CompositionMode_Source)
        pen = self.painter.pen()
        pen.setColor(self.brush_opacity)
        self.painter.setPen(pen)
        brush = self.painter.brush()
        brush.setStyle(Qt.SolidPattern)
        brush.setColor(self.brush_opacity)
        self.painter.setBrush(brush)
        self.setOpacity(0.75)

        self.edited = False
        self.lbtn_pressed = False

    def mousePressEvent(self, event):
        """
        :type event: PySide.QtGui.QGraphicsSceneMouseEvent
        """
        super(MaskCanvas, self).mousePressEvent(event)

        if event.button() == Qt.LeftButton:
            event.accept()
            self.lbtn_pressed = True
            self.edited = True

            pos = event.scenePos()
            x = pos.x()
            y = pos.y()

            if self.brush_type == MaskCanvas.RECTANGLE:
                self.painter.drawRect(QRectF(x - self.brush_hsize, y - self.brush_hsize, self.brush_size, self.brush_size))
            elif self.brush_type == MaskCanvas.CIRCLE:
                self.painter.drawEllipse(QRectF(x - self.brush_hsize, y - self.brush_hsize, self.brush_size, self.brush_size))
            else:
                raise NotImplementedError("Unknown brush type!")

            self.setPixmap(QPixmap.fromImage(self.image))

    def mouseMoveEvent(self, event):
        """
        :type event: PySide.QtGui.QGraphicsSceneMouseEvent
        """
        if self.lbtn_pressed:
            pos = event.scenePos()
            x = pos.x()
            y = pos.y()

            if self.brush_type == MaskCanvas.RECTANGLE:
                self.painter.drawRect(QRectF(x - self.brush_hsize, y - self.brush_hsize, self.brush_size, self.brush_size))
            elif self.brush_type == MaskCanvas.CIRCLE:
                self.painter.drawEllipse(QRectF(x - self.brush_hsize, y - self.brush_hsize, self.brush_size, self.brush_size))
            else:
                raise NotImplementedError("Unknown brush type!")

            self.setPixmap(QPixmap.fromImage(self.image))

    def mouseReleaseEvent(self, event):
        """
        :type event: PySide.QtGui.QGraphicsSceneMouseEvent
        """
        super(MaskCanvas, self).mouseReleaseEvent(event)

        if event.button() == Qt.LeftButton:
            self.lbtn_pressed = False

    def changeBrushSize(self, size):
        """
        :param size: must be odd number
        :type size: int
        :raise AttributeError: When brush size is not odd number
        """
        self.brush_size = size
        self.brush_hsize = size / 2.0

    def changeBrushOpacity(self, value):
        """
        :param value: Must be number in range [1, 255]
        :type value: int
        :raise AttributeError: When opacity is out of range.
        """
        if not (1 <= value <= 255):
            raise AttributeError("Brush opacity must be value in range [0, 255]")

        red, green, blue = self.rgb_color
        self.brush_opacity = QColor(red, green, blue, value)

        pen = self.painter.pen()
        pen.setColor(self.brush_opacity)
        self.painter.setPen(pen)
        brush = self.painter.brush()
        brush.setColor(self.brush_opacity)
        self.painter.setBrush(brush)

    def changeBrushType(self, type):
        """
        :type type: int
        """
        self.brush_type = type

    def cleanUp(self):
        """
        Releases painter resource
        """
        self.painter.end()


class AnnotationMask(QGraphicsPixmapItem):

    def __init__(self, image, width, height, scene):
        """
        :type image: PySide.QtGui.QImage
        :type scene: tovian.gui.components.graphics.GraphicsScene
        """
        self.image = image
        self.pixmap = QPixmap.fromImage(image).scaled(width, height, Qt.IgnoreAspectRatio, Qt.FastTransformation)
        super(AnnotationMask, self).__init__(self.pixmap)

        self.width = width
        self.height = height


class GraphicsScene(QGraphicsScene):
    """
    Custom QGraphicsScene. Handles mouse events and highlight selected items.
    When mouse event on QGraphicsView, QGraphicsView won't send this event to QMainWindow.
    So it needs to be custom mouse event handler, which sends mouse event to QMainWindow.
    """

    # signals
    btnForDrawingPressed = Signal(QGraphicsSceneMouseEvent)
    btnForDrawingMoved = Signal(QGraphicsSceneMouseEvent)
    btnForDrawingReleased = Signal(QGraphicsSceneMouseEvent)
    noObjectIsSelected = Signal()
    viewResized = Signal()              # QGraphicsView was resize
    mouseZoom = Signal(int)
    geometryChanged = Signal(QAbstractGraphicsShapeItem, QPointF)

    video_size = QSize(0, 0)
    mouse_in_item = False
    drawing_mode = False
    is_btn_for_drawing_pressed = False                           # mouse is down flag

    def __init__(self, parent):
        """
        :param parent: parent object
        :type parent: tovian.gui.GUIForms.MainApp.MainApp
        """
        super(GraphicsScene, self).__init__(parent)
        self.view = parent.graphicsView

        self.selectionChanged.connect(self.markItems)

    @Slot()
    def markItems(self):
        """
        Highlight selected items.
        """
        # reset default color
        for item in self.items():
            if not isinstance(item, AnnotationBaseClass):
                continue            # if there is an object which is not inherited from QAbstractGraphicsShapeItem

            if not item.activeInFrame():
                item.markAsNotActive()
            elif item.isSelected():
                item.markAsSelected()
            else:
                item.markAsDefault()

    def setMovable(self, state):
        """
        Enables or disables the movement of annotation objects.
        :type state: bool
        """
        for item in self.items():
            if not isinstance(item, AnnotationBaseClass):
                continue
            item.setFlag(QGraphicsItem.ItemIsMovable, state)

    def clearScene(self, deleted_items=None):
        """
        Clears graphics all objects from scene or only given objects except the video widget
        :param deleted_items: deleted objects
        :type deleted_items: list of tovian.gui.Components.graphics.AnnotationBaseClass
        """
        scene_items = self.items()
        if not len(scene_items) > 1:
            return

        if deleted_items is None:
            for item in scene_items:
                if isinstance(item, AnnotationBaseClass):
                    self.removeItem(item)
        else:
            for item in deleted_items:
                if item in scene_items and isinstance(item, AnnotationBaseClass):
                    self.removeItem(item)

    def scaleItemsPen(self, zoom):
        """
        Changes items border width and anchor size depending on current zoom value
        :param zoom: current zoom
        :type zoom: float
        """
        for item in self.items():
            if isinstance(item, AnnotationBaseClass):
                item.updateAfterScale(zoom)

    def stackClosestItemOnTop(self, cursor):
        """
        When mouse moves, it checks if any item contains cursor.
        If so, the item, which edge is closest to cursor, is stacked on top (zValue) so it could by selected by mouse.
        :param cursor: current cursor position
        :type cursor: PySide.QtCore.QPointF
        """
        # TODO check and optimize to scene.items(cursor.pos())

        contained_items = []
        z_values = []
        for item in self.items():
            z_values.append(item.zValue())
            if isinstance(item, AnnotationBaseClass):
                rect = item.boundingRect()
                rect = item.mapRectToScene(rect)
                # if cursor is inside the item
                if rect.contains(cursor):
                    dist_to_right = abs(rect.right() - cursor.x())
                    dist_to_left = abs(cursor.x() - rect.left())
                    dist_to_top = abs(rect.top() - cursor.y())
                    dist_to_bottom = abs(cursor.y() - rect.bottom())
                    min_dist = min(dist_to_left, dist_to_right, dist_to_top, dist_to_bottom)
                    # store minimal distance to edge
                    contained_items.append((min_dist, item))

        if contained_items:
            closestItem = min(contained_items, key=itemgetter(0))[1]
            closestItem.setZValue(max(z_values) + 1)

            self.mouse_in_item = True
        else:
            self.mouse_in_item = False

    def mousePressEvent(self, event):
        """
        :type event: PySide.QtGui.QGraphicsSceneMouseEvent
        """
        super(GraphicsScene, self).mousePressEvent(event)

        # if some graphics object is clicked
        clicked_items = self.items(event.scenePos())
        some_gra_object = False
        for item in clicked_items:
            if isinstance(item, AnnotationBaseClass):
                some_gra_object = True
                break

        # if no object is clicked  => call clear selection
        if not some_gra_object:
            self.noObjectIsSelected.emit()

        # for drawing purposes
        if self.drawing_mode and event.button() == Qt.LeftButton:
            self.is_btn_for_drawing_pressed = True
            self.btnForDrawingPressed.emit(event)

        else:
            # enable draq scroll if scrollbars are active
            if self.parent().zoom > 1 and not self.mouse_in_item:
                self.view.setDragMode(QGraphicsView.ScrollHandDrag)

    def mouseMoveEvent(self, event):
        """
        :type event: PySide.QtGui.QGraphicsSceneMouseEvent
        """
        super(GraphicsScene, self).mouseMoveEvent(event)

        # because when mouse tracking is enabled, signal is emited even when mouse is not pressed
        if self.drawing_mode and self.is_btn_for_drawing_pressed:
            self.btnForDrawingMoved.emit(event)
        else:
            self.stackClosestItemOnTop(event.scenePos())

    def mouseReleaseEvent(self, event):
        """
        :type event: PySide.QtGui.QGraphicsSceneMouseEvent
        """
        super(GraphicsScene, self).mouseReleaseEvent(event)

        if self.is_btn_for_drawing_pressed and event.button() == Qt.LeftButton:
            self.is_btn_for_drawing_pressed = False
            self.btnForDrawingReleased.emit(event)
        else:
            # disable draq scroll if scrollabars are active
            if self.parent().zoom > 1:
                self.view.setDragMode(QGraphicsView.NoDrag)

    def wheelEvent(self, event):
        """
        :type event: PySide.QtGui.QGraphicsSceneWheelEvent
        """
        super(GraphicsScene, self).wheelEvent(event)

        if event.orientation() is Qt.Vertical:
            event.accept()
            self.mouseZoom.emit(event.delta() / 12)

    def getVideoSize(self):
        """
        Return size of video widget on the scene.
        :rtype: PySide.QtCore.QSize
        """
        return self.video_size


class Drawing(QObject):
    """
    Class provides drawing annotation objects.
    """

    RECTANGLE = 1
    CIRCLE = 2
    MASK = 3
    POINT = 4

    def __init__(self, scene, objectID, options, parent):
        """
        :param scene: Scene of QGraphicsView
        :param objectID: ID identifies the object
        :param options: options for the object
        :type scene: PySide.QtGui.QGraphicsScene
        :type objectID: int
        :type options: dict
        """
        super(Drawing, self).__init__(parent)
        self.scene = scene
        self.object_id = objectID
        self.color = options
        self.point1 = None
        self.point2 = None
        self.graphics_object = None

    def draw(self, point, zoom, last_drawing=False):
        """
        Method will draw specific object (by ID) on the scene.
        On very last calling, lastDrawing is True.
        :param zoom: current video zoom
        :param point: mouse position
        :param last_drawing: tells when this is last drawing
        :type point: PySide.QtCore.QPointF
        :type zoom: float
        :type last_drawing: bool
        """
        if self.graphics_object:
            self.scene.removeItem(self.graphics_object)

        # Sets coordinates of top left and bottom right corners.
        self.point2 = point
        if self.point1 is None:         # if top left point is not defined yet
            self.point1 = point

        new_width = self.point2.x() - self.point1.x()
        new_height = self.point2.y() - self.point1.y()
        width = new_width if new_width > AnnotationBaseClass.MIN_WIDTH else AnnotationBaseClass.MIN_WIDTH
        height = new_height if new_height > AnnotationBaseClass.MIN_HEIGHT else AnnotationBaseClass.MIN_HEIGHT

        x = self.point1.x() + width / 2.0
        y = self.point1.y() + height / 2.0

        # which annotation tool is drawn
        if self.object_id == Drawing.RECTANGLE:
            self.graphics_object = AnnotationRect(x, y, width, height, self.scene, color=self.color)
        elif self.object_id == Drawing.CIRCLE:
            self.graphics_object = AnnotationCircle(x, y, width, self.scene, color=self.color)
        elif self.object_id == Drawing.POINT:
            self.graphics_object = AnnotationPoint(self.point1.x(), self.point1.y(), self.scene, color=self.color)
        elif self.object_id == Drawing.MASK:
            self.graphics_object = AnnotationRect(x, y, width, height, self.scene)

        self.graphics_object.updateAfterScale(zoom)
        self.graphics_object.setAcceptHoverEvents(last_drawing)       # disable resizing hover events when drawing
        self.graphics_object.setSelected(last_drawing)                # when drawn, set selected
        self.scene.addItem(self.graphics_object)

    def cancel(self):
        """
        When drawing is canceled, unfinished graphics object needs to be deleted
        """
        if self.graphics_object:
            self.scene.removeItem(self.graphics_object)
