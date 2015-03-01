"""
Unspecific gui classes
"""

from PyQt5.QtCore import pyqtSignal, Qt, QPointF, QRect, QRectF
from PyQt5.QtWidgets import QGraphicsView, QRubberBand


class RubberbandSelectionQGraphicsView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(self.scene)
        self.rubberBand = OriginQRubberBand(QRubberBand.Rectangle, self)
        self.rubberBand.selected.connect(self.on_rubberband_selected)

    rect_in_scene_selected = pyqtSignal(QRectF)

    def on_rubberband_selected(self, rect):
        self.rect_in_scene_selected.emit(
            QRectF(self.mapToScene(rect.topLeft()),
                   self.mapToScene(rect.bottomRight()))
        )

    def mousePressEvent(self, event):
        super().mousePressEvent(event)

        if event.buttons() == Qt.LeftButton:
            self.rubberBand.start(event.pos())

        else:
            self.rubberBand.done(event.pos())

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        self.rubberBand.handle_move(event.pos())

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.rubberBand.done(event.pos())


class OriginQRubberBand(QRubberBand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.origin = None

    selected = pyqtSignal(QRect)

    def start(self, pos):
        self.origin = pos
        self.setGeometry(pos.x(), pos.y(), 0, 0)
        self.show()

    def handle_move(self, pos):
        if not self.origin:
            return

        self.resize(
            pos.x() - self.origin.x(),
            pos.y() - self.origin.y()
        )

    def done(self, pos):
        if not self.origin:
            return

        selected_rect = QRect(self.origin, pos)
        self.origin = None
        self.hide()

        self.selected.emit(selected_rect)
