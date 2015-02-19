import logging
import os
from functools import partial

from PIL.Image import Image
from PyQt5.QtCore import QObject, pyqtSignal, QThread

from .threading import QThreadedWorkerDebug as QThreadedWorker
from analyze.composition import CompositionWithProgressbar, Spectrogram
from analyze.media.sound import Sound
from utils import ProgressProxy


log = logging.getLogger(__name__)


class ProgressProxyToProgressDialog(ProgressProxy):
    def __init__(self, progress_dialog, *args, **kwargs):
        self.progress_dialog = progress_dialog
        super().__init__(*args, **kwargs)

    def start(self):
        self.progress_dialog.reset()
        self.progress_dialog.setRange(0, self.length)

    def make_step(self):
        super().make_step()

        if self.progress_dialog.wasCanceled():
            self.cancel()

    def render_progress(self):
        self.progress_dialog.setValue(self.pos)

    def done(self):
        log.debug('ProgressProxyToProgressDialog.done')

        if getattr(self, 'canceled', False):
            raise CompositionCanceled

    def cancel(self):
        self.canceled = True
        raise StopIteration


class CompositionCanceled(Exception):
    pass


class QCompositionWorker(QThreadedWorker):
    def __init__(self, progress_dialog):
        super().__init__()
        self.busy = False
        self.progress_dialog = progress_dialog
        self.process.connect(self._process)

    process = pyqtSignal(Sound)
    process_ok = pyqtSignal(Spectrogram)
    process_error = pyqtSignal(str)

    message = pyqtSignal(str)

    def set_progress_value(self, val):
        self._message('Progress value: {}'.format(val))

    def _process(self, sound):
        log.debug('Before Image processed')

        # FIXME Implement jobs queue. Just cancel previous here
        if self.busy:
            self.process_error.emit('Busi')

            return

        self.busy = True

        progressbar = partial(ProgressProxyToProgressDialog,
                              self.progress_dialog)

        self._message('Prepare composition')

        try:
            with CompositionWithProgressbar(
                progressbar, sound,
                scale_resolution=1/72, omega0=70, decimation_factor=7
            ) as composition:

                self._message('Analyse')
                spectrogram = composition.get_spectrogram()

        except CompositionCanceled:
            log.debug('Composition canceled')
            self.process_error.emit('Composition canceled')

            return

        finally:
            self.busy = False

        log.debug('Image processed')

        self.process_ok.emit(spectrogram)

    def _message(self, msg):
        self.message.emit(msg)
