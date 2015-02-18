import logging
import os
from functools import partial

from PIL.Image import Image
from PyQt5.QtCore import QObject, pyqtSignal, QThread

from .threading import QThreadedWorkerDebug as QThreadedWorker
from analyze.composition import CompositionWithProgressbar, Spectrogram
from analyze.media.sound import ChunksProvider
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
        self.composition = None
        self.progress_dialog = progress_dialog
        self.process.connect(self._process)

    process = pyqtSignal(ChunksProvider)
    process_ok = pyqtSignal(Spectrogram)
    process_error = pyqtSignal(str)

    message = pyqtSignal(str)

    def set_progress_value(self, val):
        self._message('Progress value: {}'.format(val))

    def _process(self, chunks_provider):
        log.debug('Before Image processed')

        # FIXME Implement jobs queue. Just cancel previous here
        if self.composition:
            self._message('Busi')
            self.process_error.emit('Busi')

        progressbar = partial(ProgressProxyToProgressDialog,
                              self.progress_dialog)

        try:
            self.composition = CompositionWithProgressbar(
                progressbar,
                chunks_provider,
                scale_resolution=1/72,
                omega0=70,
                decimation_factor=7
            )

        except Exception:
            log.exception('Composition create error')
            self.process_error.emit('Composition create error')

            return

        self._message('Prepare composition Wavelet Box')
        # FIXME implement some sontextmanager on composition.wbox
        self.composition.prepare_wbox()
        self._message('Analyse')

        try:
            spectrogram = self.composition.get_spectrogram()

        except CompositionCanceled:
            log.debug('Composition canceled')
            self.process_error.emit('Composition canceled')

            return

        finally:
            self.composition = None

        log.debug('Image processed')

        self.process_ok.emit(spectrogram)

    def _message(self, msg):
        self.message.emit(msg)
