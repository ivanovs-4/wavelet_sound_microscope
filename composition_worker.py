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


class CompositionWorker(QObject):
    def __init__(self):
        super().__init__()
        self.thread = QThread()
        thread = self.thread
        worker = self

        worker.moveToThread(thread)
        thread.start()

        worker.finished.connect(self.worker_finished)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self.thread_finished)

    def worker_finished(self):
        log.info('Worker finished')

    def thread_finished(self):
        log.debug('Thread finished')

    def set_progress_value(self, val):
        self.update_status('Progress value: {}'.format(val))

    def load_file(self, fname):
        self.update_status('Loading...')

        from composition import CompositionProgress

        log.info('CompositionWorker.load_file: %s', fname)

        self.fname = fname

        progress = partial(DummyProgressbar, setter=self.set_progress_value)

        try:
            self.composition = CompositionProgress(fname, progress)

        except Exception as e:
            log.error('Create composition error: %s', repr(e))
            self.update_status(repr(e))
            self.loading_file_error.emit()

            return

        else:
            log.info('Create composition ok')
            self.update_status('Opened {0}'.format(os.path.basename(fname)))
            self.loading_file_ok.emit()

    def process(self):
        log.debug('Before Image processed')

        self.update_status('Prepare composition Wavelet Box')
        self.composition.prepare_wbox()

        self.update_status('Analyse')
        image = self.composition.get_image()
        log.debug('Image processed')
        self.processed.emit(image)
        self.update_status('Done')

    loading_file_ok = pyqtSignal()
    loading_file_error = pyqtSignal()

    processed = pyqtSignal(Image)
    message = pyqtSignal(str)

    def update_status(self, msg):
        self.message.emit(msg)

    finished = pyqtSignal()

    def finish(self):
        self.finished.emit()
