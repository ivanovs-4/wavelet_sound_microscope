"""
Unspecific gui classes
"""

from PyQt5.QtCore import pyqtSignal, Qt, QPoint, QPointF, QRect, QRectF
from PyQt5.QtWidgets import QGraphicsView, QRubberBand


class RubberbandSelectionQGraphicsView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(self.scene)
        self.rubberBand = OriginQRubberBand(QRubberBand.Rectangle, self)
        self.rubberBand.selected.connect(self.rect_selected.emit)

    rect_selected = pyqtSignal(QRect)

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

        x1, x2 = sorted([self.origin.x(), pos.x()])
        y1, y2 = sorted([self.origin.y(), pos.y()])
        self.setGeometry(QRect(QPoint(x1, y1), QPoint(x2, y2)))

    def done(self, pos):
        if not self.origin:
            return

        selected_rect = QRect(self.origin, pos)
        self.origin = None
        self.hide()

        self.selected.emit(selected_rect)
