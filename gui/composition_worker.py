import collections
import logging
import os
from functools import partial

from PIL.Image import Image
from PyQt5.QtCore import QObject, pyqtSignal, QThread


log = logging.getLogger(__name__)


class DummyProgressbar(collections.Iterator):
    def __init__(self, iterable, setter, length=None, label=None):
        self.setter = setter
        self.counter = 0

        self.iterable = iterable

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        pass

    def __iter__(self):
        return self

    def __next__(self):
        self.counter += 1
        self.setter('Pos {}'.format(self.counter))

        return next(self.iterable)


class QThreadedWorker(QObject):
    def __init__(self):
        super().__init__()
        self.thread = QThread()

        self.moveToThread(self.thread)
        self.thread.start()

        # Thread initialisation
        self.finish.connect(self.thread.quit)
        self.finish.connect(self.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        # For debug threading
        self.finish.connect(self._finish)
        self.thread.finished.connect(self._thread_finished)

    def _finish(self):
        log.info('Worker finished')

    def _thread_finished(self):
        log.debug('Thread finished')


class QCompositionWorker(QThreadedWorker):
    def __init__(self):
        super().__init__()
        self.load_file.connect(self._load_file)
        self.process.connect(self._process)

    load_file = pyqtSignal(str)
    load_file_ok = pyqtSignal()
    load_file_error = pyqtSignal()

    process = pyqtSignal()
    process_ok = pyqtSignal(Image)

    message = pyqtSignal(str)

    finish = pyqtSignal()

    def set_progress_value(self, val):
        self._message('Progress value: {}'.format(val))

    def _load_file(self, fname):
        self._message('Loading...')

        from analyze.composition import CompositionWithProgressbar

        log.info('CompositionWorker._load_file: %s', fname)

        self.fname = fname

        progressbar = partial(DummyProgressbar, setter=self.set_progress_value)

        try:
            self.composition = CompositionWithProgressbar(fname, progressbar)

        except Exception as e:
            log.error('Create composition error: %s', repr(e))
            self._message(repr(e))
            self.load_file_error.emit()

            return

        else:
            log.info('Create composition ok')
            self._message('Opened {0}'.format(os.path.basename(fname)))
            self.load_file_ok.emit()

    def _process(self):
        log.debug('Before Image processed')

        self._message('Prepare composition Wavelet Box')
        self.composition.prepare_wbox()

        self._message('Analyse')
        image = self.composition.get_image()
        log.debug('Image processed')
        self.process_ok.emit(image)
        self._message('Done')

    def _message(self, msg):
        self.message.emit(msg)
