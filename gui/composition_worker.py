import logging
import os
from functools import partial

from PIL.Image import Image
from PyQt5.QtCore import QObject, pyqtSignal, QThread

from .threading import QThreadedWorkerDebug as QThreadedWorker
from analyze.composition import CompositionWithProgressbar
from analyze.media.sound import ChunksProviderFromSoundFile
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

        self.progress_dialog = progress_dialog

        self.load_file.connect(self._load_file)
        self.process.connect(self._process)

    load_file = pyqtSignal(str)
    load_file_ok = pyqtSignal()
    load_file_error = pyqtSignal()

    process = pyqtSignal()
    process_ok = pyqtSignal(Image)
    process_error = pyqtSignal()

    message = pyqtSignal(str)

    def set_progress_value(self, val):
        self._message('Progress value: {}'.format(val))

    def _load_file(self, fname):
        self._message('Loading...')

        log.debug('CompositionWorker._load_file: %s', fname)

        self.fname = fname

        try:
            self.chunks_provider = ChunksProviderFromSoundFile(fname)

        except Exception as e:
            log.exception('Load file error: %s', repr(e))
            self._message(repr(e))
            self.load_file_error.emit()

        else:
            log.debug('Load file ok')
            self._message('Opened {0}'.format(os.path.basename(fname)))
            self.load_file_ok.emit()

    def _process(self):
        log.debug('Before Image processed')

        progressbar = partial(ProgressProxyToProgressDialog,
                              self.progress_dialog)

        try:
            self.composition = CompositionWithProgressbar(
                progressbar,
                self.chunks_provider,
                scale_resolution=1/72,
                omega0=70,
                decimation_factor=7
            )

        except Exception:
            log.exception('Composition create error')
            self._message('Composition create error')
            self.process_error.emit()

            return

        self._message('Prepare composition Wavelet Box')
        self.composition.prepare_wbox()
        self._message('Analyse')

        try:
            image = self.composition.get_image()

        except CompositionCanceled:
            log.debug('Composition canceled')
            self._message('Composition canceled')
            self.process_error.emit()

            return

        log.debug('Image processed')
        self.process_ok.emit(image)
        self._message('Done')

    def _message(self, msg):
        self.message.emit(msg)
