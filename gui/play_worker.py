import logging

from PyQt5.QtCore import pyqtSignal

from .threading import QThreadedWorkerDebug as QThreadedWorker
from analyze.media.sound import Sound


log = logging.getLogger(__name__)


class QPlayWorker(QThreadedWorker):
    def __init__(self):
        super().__init__()
        self.busy = False
        self.play.connect(self._play)

    play = pyqtSignal(Sound)

    def _play(self, sound):
        if self.busy:
            # Do nothing when busy
            return

        self.busy = True

        try:
            sound.play()

        except Exception:
            log.exception('Play error')

        finally:
            self.busy = False
