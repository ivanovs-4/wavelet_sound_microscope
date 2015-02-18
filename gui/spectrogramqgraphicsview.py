import logging

from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QPixmap, QImage
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsView, QRubberBand

log = logging.getLogger(__name__)


class SpectrogramQGraphicsView(QGraphicsView):
    def __init__(self):
        self.scene = QGraphicsScene()
        # scene.setItemIndexMethod(QGraphicsScene.NoIndex)

        super(SpectrogramQGraphicsView, self).__init__(self.scene)

        self.setRenderHint(QPainter.Antialiasing)

        # self.setCacheMode(QGraphicsView.CacheBackground)
        # self.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)

        # self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setDragMode(QGraphicsView.ScrollHandDrag)

        # self.setMouseTracking(True)

        self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)

    def update_spectrogram(self, spectrogram):
        self.show_image(spectrogram.image)

    def show_image(self, im):
        if im.mode != 'RGB':
            im = im.convert('RGB')

        # buf_data = im.tostring('raw', 'BGRX')
        # image = QImage(buf_data, im.size[0], im.size[1],
        #                QImage.Format_RGB32)

        im.save('/tmp/spectrogram.png')
        image = QImage('/tmp/spectrogram.png')

        self.scene.clear()
        self.scene.addPixmap(QPixmap.fromImage(image))

    def mousePressEvent(self, event):
        log.debug('mousePressEvent %r', event)

#     if (event.button() == Qt::MiddleButton) {
        self.rubberBandOrigin = event.pos()
        self.rubberBand.setGeometry(event.x(), event.y(), 0, 0)
        log.debug('rubberBand %r', self.rubberBand)
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
        view = self

        rubberBandEnd = event.pos()
        zoomRectInScene = QRectF(
            view.mapToScene(self.rubberBandOrigin),
            view.mapToScene(rubberBandEnd)
        )
        center = zoomRectInScene.center()
        view.fitInView(zoomRectInScene, Qt.KeepAspectRatio)
        self.rubberBandActive = False
        # log.debug('rubberBand %r', dir(self.rubberBand))
        self.rubberBand.hide()
#         delete rubberBand
#     }
#     else{
#         LastPanPoint = QPoint()
#     }
# }



# void MyGraphics::wheelEvent(QWheelEvent *event){
#     if(event->delta() > 0){
#         //Zoom in
#         this->zoomIn();
#     } else {
#         this->zoomOut();
#     }
# }
# /*
# void MyGraphics::mousePressEvent(QMouseEvent *event)
# {
#     if (event->button() == Qt::MiddleButton) {
#         rubberBandOrigin = event->pos();
#         rubberBand = new QRubberBand(QRubberBand::Rectangle, this);
#         rubberBand->setGeometry(event->x(),event->y(),0, 0);
#         rubberBand->show();
#         rubberBandActive = true;
#     }
#     if(event->button() == Qt::LeftButton){
#         LastPanPoint = event->pos();
#     }
# }
# void MyGraphics::mouseMoveEvent(QMouseEvent *event)
# {
#     if (event->buttons() == Qt::MiddleButton && rubberBandActive == true){
#         rubberBand->resize( event->x()-rubberBandOrigin.x(), event->y()-rubberBandOrigin.y() );
#     }
#     else{
#         if(!LastPanPoint.isNull()) {
#             //Get how much we panned
#             QGraphicsView * view = static_cast<QGraphicsView *>(this);
#             QPointF delta = view->mapToScene(LastPanPoint) - view->mapToScene(event->pos());
#             LastPanPoint = event->pos();
#         }
#     }
# }
# void MyGraphics::mouseReleaseEvent(QMouseEvent *event)
# {
#    if (event->button() == Qt::MiddleButton){
#         QGraphicsView * view = static_cast<QGraphicsView *>(this);
#         QPoint rubberBandEnd = event->pos();
#         QRectF zoomRectInScene = QRectF(view->mapToScene(rubberBandOrigin), view->mapToScene(rubberBandEnd));
#         QPointF center = zoomRectInScene.center();
#         view->fitInView(zoomRectInScene, Qt::KeepAspectRatio);
#         rubberBandActive =  false;
#         delete rubberBand;
#     }
#     else{
#         LastPanPoint = QPoint();
#     }
# }
# */
