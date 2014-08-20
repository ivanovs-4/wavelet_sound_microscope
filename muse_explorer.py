#!/usr/bin/python3
import logging
import os
import sys
from contextlib import contextmanager
from functools import partial
from PIL.Image import Image

from PyQt5.QtCore import QSettings, QTimer, QVariant, QFile, QObject, pyqtSlot, pyqtSignal, QThread
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QApplication, QLabel, QFileDialog, QFrame

from gui.helperqmainwindow import HelperQMainWindow
from gui.spectrogramqgraphicsview import SpectrogramQGraphicsView


__version__ = '1.0.0'

logging.basicConfig()
logging.getLogger('').setLevel(logging.DEBUG)

log = logging.getLogger(__name__)


@contextmanager
def statusbar(val):
    log.debug('Status before %s', val)
    yield
    log.debug('Status after %s', val)


class CompositionWorker(QObject):
    def __init__(self, filename):
        self.filename = filename
        super().__init__()

    @pyqtSlot()
    def process(self):
        from composition import Composition
        log.debug('Before Image processed')
        self.composition = Composition(self.filename)

        with statusbar('Prepare composition Wavelet Box'):
            self.composition.prepare_wbox()

        image = self.composition.get_image()
        log.debug('Image processed')
        self.processed.emit(image)
        self.finished.emit()

    processed = pyqtSignal(Image)
    finished = pyqtSignal()


class MainWindow(HelperQMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.filename = None

        self.spectrogram = SpectrogramQGraphicsView()
        self.spectrogram.setMinimumSize(200, 200)
        self.setCentralWidget(self.spectrogram)

        self.size_label = QLabel()
        self.size_label.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        status = self.statusBar()
        status.setSizeGripEnabled(False)
        status.addPermanentWidget(self.size_label)
        status.showMessage('Ready', 5000)

        file_open_action = self.create_action(
            '&Open...', self.file_open, QKeySequence.Open, 'fileopen',
            'Open an existing image file'
        )

        file_quit_action = self.create_action(
            '&Quit', self.close, 'Ctrl+Q', 'filequit', 'Close the application'
        )

        file_toolbar = self.addToolBar('File')
        file_toolbar.setObjectName('file_tool_bar')

        self.add_actions(file_toolbar, (
            file_open_action,
            file_quit_action,
        ))

        settings = QSettings()
        self.restoreGeometry(settings.value('MainWindow/Geometry', ''))
        self.restoreState(settings.value('MainWindow/State', ''))

        QTimer.singleShot(0, self.load_initial_file)

    def file_open(self):
        if not self.ok_to_continue():
            return

        path = (os.path.dirname(self.filename)
               if self.filename is not None else '.')
        formats = ['*.wav', '*.flac']

        fname, fmts = QFileDialog.getOpenFileName(
            self,
            'Musical harmony - Choose Music file',
            path,
            'Sound files ({0})'.format(' '.join(formats))
        )

        if fname:
            self.load_file(fname)

    def load_file(self, fname):
        self.filename = fname

        # try:
        #     self.composition = Composition(fname)

        # except Exception as e:
        #     self.update_status(repr(e))

        # else:
        #     self.update_status('Opened {0} ...'.format(os.path.basename(fname)))
        #     self.update_spectrogram()

        # if not self.composition:
            # return

        self.worker = CompositionWorker(self.filename)
        log.debug('Worker created')
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.process)
        # self.worker.finished.connect(self.thread.quit)
        # self.worker.finished.connect(self.worker.deleteLater)
        # self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self.thread_finished)
        self.worker.processed.connect(self.update_spectrogram)
        self.thread.start()
        log.debug('Thread started')

    def thread_finished(self):
        log.debug('Thread finished')

    def update_spectrogram(self, image):
        log.debug('Run update_spectrogram %s', image)
        self.spectrogram.show_image(image)

    def load_initial_file(self):
        settings = QSettings()
        fname = settings.value('LastFile')
        if fname and QFile.exists(fname):
            self.load_file(fname)

    def update_status(self, message):
        self.statusBar().showMessage(message, 5000)

    def closeEvent(self, event):
        if self.ok_to_continue():
            settings = QSettings()
            if self.filename:
                settings.setValue("LastFile", self.filename)
            settings.setValue('MainWindow/Geometry',
                              QVariant(self.saveGeometry()))
            settings.setValue('MainWindow/State',
                              QVariant(self.saveState()))
        else:
            event.ignore()

    def ok_to_continue(self):
        return True


def main():
    app = QApplication(sys.argv)
    app.setOrganizationName('Sergey Ivanov')
    app.setOrganizationDomain('')
    app.setApplicationName('Musical harmony explorer')
    form = MainWindow()
    form.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
