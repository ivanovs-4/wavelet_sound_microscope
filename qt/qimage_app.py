#!/usr/bin/python3
# -*- coding: utf-8 -*-

from PyQt5.QtCore import (
    qAbs,
    QLineF,
    QPointF,
    QRectF,
    qrand,
    qsrand,
    Qt,
    QTime,
    QTimer)
from PyQt5.QtGui import (
    QBrush,
    QColor,
    QPainter,
    QPainterPath,
    QPixmap,
    QPolygonF)
from PyQt5.QtWidgets import (
    QApplication,
    QGraphicsItem,
    QGraphicsScene,
    QGraphicsView,
    QGraphicsWidget)


if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)
    qsrand(QTime(0, 0, 0).secsTo(QTime.currentTime()))

    scene = QGraphicsScene()
    # scene.setItemIndexMethod(QGraphicsScene.NoIndex)

    scene.addPixmap(QPixmap('sample.jpg'))

    view = QGraphicsView(scene)
    view.setRenderHint(QPainter.Antialiasing)

    # view.setCacheMode(QGraphicsView.CacheBackground)

    # view.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)
    view.setDragMode(QGraphicsView.RubberBandDrag)

    view.setWindowTitle('Wavelet Sound Microscope')

    view.show()

    sys.exit(app.exec_())
