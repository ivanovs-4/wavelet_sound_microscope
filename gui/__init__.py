"""
Unspecific gui classes
"""

from PyQt5.QtCore import pyqtSignal, Qt, QPointF, QRectF
from PyQt5.QtWidgets import QGraphicsView, QRubberBand


class RubberbandSelectionQGraphicsView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(self.scene)
        self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)

    rect_in_scene_selected = pyqtSignal(QRectF)

    def mousePressEvent(self, event):
#     if (event.button() == Qt::MiddleButton) {
        self.rubberBandOrigin = event.pos()
        self.rubberBand.setGeometry(event.x(), event.y(), 0, 0)
        self.rubberBand.show()
        self.rubberBandActive = True
#     }
#     if(event.button() == Qt::LeftButton){
#         LastPanPoint = event.pos()
#     }
# }

    def mouseMoveEvent(self, event):
# {
#     if (event.buttons() == Qt::MiddleButton && rubberBandActive == true){
        if getattr(self, 'rubberBandActive', False):
            self.rubberBand.resize(
                event.x() - self.rubberBandOrigin.x(),
                event.y() - self.rubberBandOrigin.y()
            )
#     }
#     else{
#         if(!LastPanPoint.isNull()) {
#             //Get how much we panned
#             QGraphicsView * view = static_cast<QGraphicsView *>(this)
#             QPointF delta = view.mapToScene(LastPanPoint) - view.mapToScene(event.pos())
#             LastPanPoint = event.pos()
#         }
#     }
# }

    def mouseReleaseEvent(self, event):
# {
#    if (event.button() == Qt::MiddleButton){
#         QGraphicsView * view = static_cast<QGraphicsView *>(this)
        rubberBandEnd = event.pos()

        selectedRectInScene = QRectF(
            self.mapToScene(self.rubberBandOrigin),
            self.mapToScene(rubberBandEnd)
        )

        self.rect_in_scene_selected.emit(selectedRectInScene)
        self.rubberBandActive = False
        self.rubberBand.hide()
#     }
#     else{
#         LastPanPoint = QPoint()
#     }
# }


