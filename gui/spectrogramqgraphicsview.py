import logging

import numpy as np
from PyQt5.QtCore import pyqtSignal, Qt, QPointF, QRectF
from PyQt5.QtGui import QPainter, QPixmap, QImage, QBrush, QColor, QPen
from PyQt5.QtWidgets import QGraphicsScene

from . import RubberbandSelectionQGraphicsView
from analyze.media.notes import HARMONIC_COLORS, INTERVALS, NOTES_COLORS
from analyze.media.sound import SoundFragment


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
        el = self.addEllipse(QRectF(-size/2, -size/2, size, size), **kwargs)
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
        self.rect_selected.connect(self.on_rect_selected)

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

    def on_rect_selected(self, rect):
        if not self.spectrogram:
            return

        scene_rect = QRectF(
            self.mapToScene(rect.topLeft()),
            self.mapToScene(rect.bottomRight())
        )

        self.scene.set_selection(scene_rect)

        fragment = self.spectrogram.get_sound_fragment(
            (scene_rect.left(), scene_rect.right()),
            (scene_rect.bottom(), scene_rect.top()),
        )

        self.fragment_selected.emit(fragment)

    def deal_with_harmonics(self, pos):
        """ Harmonics show prototype """
        scene_pos = self.mapToScene(pos)

        closer_rect = QRectF(
            QPointF(scene_pos.x() - 3, scene_pos.y() - 12),
            QPointF(scene_pos.x() + 3, scene_pos.y() + 12),
        )
        loudest_pos = self.where_loudest_in_rect(closer_rect)

        sc = self.scene
        sc.reset_harmonics()
        sc.add_harmonic(loudest_pos, size=8, brush=QBrush(QColor(255, 0, 0)))

        selected_x = loudest_pos.x()
        selected_f = self.spectrogram.y2freq(loudest_pos.y())

        # Octava
        for name, interval in INTERVALS.items():
            if interval == int(interval):
                continue

            sc.add_harmonic(
                QPointF(
                    selected_x,
                    self.spectrogram.freq2y(selected_f * interval)
                ),
                size=4, brush=QBrush(QColor(NOTES_COLORS[name]))
            )

            sc.add_harmonic(
                QPointF(
                    selected_x,
                    self.spectrogram.freq2y(selected_f * interval / 2)
                ),
                size=4, brush=QBrush(QColor(NOTES_COLORS[name]))
            )

        # Upper
        for h in list(HARMONIC_COLORS.keys())[1:25]:
            y2 = self.spectrogram.freq2y(selected_f * h)

            sc.add_harmonic(
                QPointF(selected_x, y2),
                size=4,
                brush=QBrush(QColor(HARMONIC_COLORS[h]))
            )

        # Lower
        for h in range(2, 14):
            y2 = self.spectrogram.freq2y(selected_f / h)

            sc.add_harmonic(
                QPointF(selected_x, y2),
                size=4,
                brush=QBrush(QColor('#bbb'))
            )

    def where_loudest_in_rect(self, rect):
        x1 = rect.left()
        x2 = rect.right()
        y1 = rect.top()
        y2 = rect.bottom()

        abs_rect = self.spectrogram.abs_image[y1:y2+1, x1:x2+1]

        peak_index = np.unravel_index(abs_rect.argmax(), abs_rect.shape)
        y, x = peak_index

        return QPointF(x1 + x, y1 + y)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)

        if event.buttons() == Qt.RightButton:
            self.deal_with_harmonics(event.pos())


# void MyGraphics::wheelEvent(QWheelEvent *event){
#     if(event->delta() > 0){
#         //Zoom in
#         this->zoomIn();
#     } else {
#         this->zoomOut();
#     }
# }
