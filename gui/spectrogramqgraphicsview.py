import logging

import numpy as np
from PyQt5.QtCore import pyqtSignal, Qt, QPointF, QRectF
from PyQt5.QtGui import QPainter, QPixmap, QImage, QBrush, QColor
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsView, QRubberBand


log = logging.getLogger(__name__)


class SoundFragment(object):
    def __init__(self, time, frequency):
        self.time = tuple(sorted(time))
        self.frequency = tuple(sorted(frequency))


class SpectrogramQGraphicsView(QGraphicsView):
    def __init__(self):
        self.spectrogram = None
        self.scene = QGraphicsScene()
        # scene.setItemIndexMethod(QGraphicsScene.NoIndex)

        super().__init__(self.scene)

        self.setRenderHint(QPainter.Antialiasing)

        # self.setCacheMode(QGraphicsView.CacheBackground)
        # self.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)

        # self.setDragMode(QGraphicsView.RubberBandDrag)
        # self.setDragMode(QGraphicsView.ScrollHandDrag)

        # self.setMouseTracking(True)

        self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)

    fragment_selected = pyqtSignal(SoundFragment)

    def update_spectrogram(self, spectrogram):
        self.spectrogram = spectrogram
        self.show_image(spectrogram.image)

    def reset(self):
        self.spectrogram = None
        self.scene.clear()

        # FIXME Create some abstract tool for mouse events handling
        self.rubberBandActive = False
        self.rubberBand.hide()

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

    def selected_rect_in_scene(self, rect):
        if not self.spectrogram:
            return

        loudest_pos = self.where_loudest_in_rect(rect)

        el = self.scene.addEllipse(QRectF(-7, -7, 7, 7), brush=QBrush(QColor(255, 0, 0)))
        el.setPos(loudest_pos)

        # Harmonics show prototype
        for j in range(12):
            f = self.spectrogram.y2freq(loudest_pos.y())
            y2 = self.spectrogram.freq2y(f * (j + 2))
            el = self.scene.addEllipse(QRectF(-5, -5, 5, 5), brush=QBrush(QColor(255, 0, 0)))
            el.setPos(QPointF(loudest_pos.x(), y2))

        for j in range(12):
            f = self.spectrogram.y2freq(loudest_pos.y())
            y2 = self.spectrogram.freq2y(f / (j + 2))
            el = self.scene.addEllipse(QRectF(-5, -5, 5, 5), brush=QBrush(QColor(255, 255, 0)))
            el.setPos(QPointF(loudest_pos.x(), y2))

        time = (
            self.spectrogram.x2time(rect.left()),
            self.spectrogram.x2time(rect.right()),
        )

        frequency = (
            self.spectrogram.y2freq(rect.bottom()),
            self.spectrogram.y2freq(rect.top()),
        )

        self.fragment_selected.emit(SoundFragment(time, frequency))

    def where_loudest_in_rect(self, rect):
        x1 = rect.left()
        x2 = rect.right()
        y1 = rect.top()
        y2 = rect.bottom()

        abs_rect = self.spectrogram.abs_image[y1-1:y2, x1-1:x2]

        peak_index = np.unravel_index(abs_rect.argmax(), abs_rect.shape)
        y, x = peak_index

        return QPointF(x1 + x, y1 + y + 1)

    def mousePressEvent(self, event):
        log.debug('mousePressEvent %r', event)

        # self.rubberBand.hide()

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

        rubberBandEnd = event.pos()

        selectedRectInScene = QRectF(
            self.mapToScene(self.rubberBandOrigin),
            self.mapToScene(rubberBandEnd)
        )
        self.selected_rect_in_scene(selectedRectInScene)

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
