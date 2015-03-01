import logging

import numpy as np
from PyQt5.QtCore import pyqtSignal, Qt, QPointF, QRectF
from PyQt5.QtGui import QPainter, QPixmap, QImage, QBrush, QColor, QPen
from PyQt5.QtWidgets import QGraphicsScene

from analyze.media.sound import SoundFragment

from . import RubberbandSelectionQGraphicsView


log = logging.getLogger(__name__)


class SpectrogramQGraphicsScene(QGraphicsScene):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.selection_rect_item = None
        self.harmonics_items = []

    def clear(self):
        super().clear()
        self.selection_rect_item = None
        self.harmonics_items = []

    def set_selection(self, rect):
        if self.selection_rect_item:
            self.removeItem(self.selection_rect_item)

        self.selection_rect_item = self.addRect(
            rect, pen=QPen(QColor('#00FF00'))
        )

    def reset_harmonics(self):
        for i in self.harmonics_items:
            self.removeItem(i)

        self.harmonics_items = []

    def add_harmonic(self, pos, size, **kwargs):
        el = self.addEllipse(QRectF(-size, -size, size, size), **kwargs)
        el.setPos(pos)
        self.harmonics_items.append(el)


class SpectrogramQGraphicsView(RubberbandSelectionQGraphicsView):
    def __init__(self):
        self.spectrogram = None
        self.scene = SpectrogramQGraphicsScene()
        # scene.setItemIndexMethod(QGraphicsScene.NoIndex)

        super().__init__(self.scene)

        self.setRenderHint(QPainter.Antialiasing)

        # self.setCacheMode(QGraphicsView.CacheBackground)
        # self.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)

        # self.setMouseTracking(True)
        self.rect_in_scene_selected.connect(self.on_rect_in_scene_selected)

    fragment_selected = pyqtSignal(SoundFragment)
    reseted = pyqtSignal()

    def update_spectrogram(self, spectrogram):
        self.spectrogram = spectrogram
        self.show_image(spectrogram.image)

    def reset(self):
        self.spectrogram = None
        self.scene.clear()

        self.reseted.emit()

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

    def on_rect_in_scene_selected(self, rect):
        if not self.spectrogram:
            return

        self.scene.set_selection(rect)

        fragment = self.spectrogram.get_sound_fragment(
            (rect.left(), rect.right()),
            (rect.bottom(), rect.top()),
        )

        self.fragment_selected.emit(fragment)

    def deal_with_harmonics(self, pos):
        scene_pos = self.mapToScene(pos)

        closer_rect = QRectF(
            QPointF(scene_pos.x() - 3, scene_pos.y() - 12),
            QPointF(scene_pos.x() + 3, scene_pos.y() + 12),
        )
        loudest_pos = self.where_loudest_in_rect(closer_rect)

        sc = self.scene
        sc.reset_harmonics()
        sc.add_harmonic(loudest_pos, size=7, brush=QBrush(QColor(255, 0, 0)))

        # Harmonics show prototype
        for j in range(12):
            f = self.spectrogram.y2freq(loudest_pos.y())
            y2 = self.spectrogram.freq2y(f * (j + 2))

            sc.add_harmonic(
                QPointF(loudest_pos.x(), y2),
                size=4,
                brush=QBrush(QColor(255, 0, 0))
            )

        for j in range(12):
            f = self.spectrogram.y2freq(loudest_pos.y())
            y2 = self.spectrogram.freq2y(f / (j + 2))

            sc.add_harmonic(
                QPointF(loudest_pos.x(), y2),
                size=4,
                brush=QBrush(QColor(255, 200, 0))
            )

    def where_loudest_in_rect(self, rect):
        x1 = rect.left()
        x2 = rect.right()
        y1 = rect.top()
        y2 = rect.bottom()

        abs_rect = self.spectrogram.abs_image[y1-1:y2, x1-1:x2]

        peak_index = np.unravel_index(abs_rect.argmax(), abs_rect.shape)
        y, x = peak_index

        return QPointF(x1 + x, y1 + y + 1)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)

        if event.buttons() == Qt.MiddleButton:
            self.deal_with_harmonics(event.pos())


# void MyGraphics::wheelEvent(QWheelEvent *event){
#     if(event->delta() > 0){
#         //Zoom in
#         this->zoomIn();
#     } else {
#         this->zoomOut();
#     }
# }
