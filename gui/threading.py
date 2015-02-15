import logging

from PyQt5.QtCore import QObject, pyqtSignal, QThread


log = logging.getLogger(__name__)


class QThreadedWorker(QObject):
    def __init__(self):
        super().__init__()
        self.thread = QThread()

        self.moveToThread(self.thread)
        self.thread.start()

        # Thread initialisation
        self.finished.connect(self.thread.quit)
        self.finished.connect(self.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

    finished = pyqtSignal()

    def finish(self):
        self.finished.emit()


class QThreadedWorkerDebug(QThreadedWorker):
    def __init__(self):
        super().__init__()
        self.finished.connect(self._finished)
        self.thread.finished.connect(self._thread_finished)

    def _finished(self):
        log.info('Worker finished')

    def _thread_finished(self):
        log.debug('Thread finished')
