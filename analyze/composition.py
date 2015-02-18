import logging

import numpy as np
from scipy.misc import toimage

from .media import apply_colormap, nolmalize_horizontal_smooth
from utils import cached_property


log = logging.getLogger(__name__)


class Composition(object):
    def __init__(self, chunks_provider,
                 scale_resolution=1/36, omega0=70, decimation_factor=9):
        self.chunks_provider = chunks_provider
        self.scale_resolution = scale_resolution
        self.omega0 = omega0
        self.decimate = self.chunks_provider.chunk_size // 2 ** decimation_factor

        self.norma_window_len = 501
        log.debug('Norma window len: %s', self.norma_window_len)

        self._wbox = None

    def __enter__(self):
        self._wbox = self._create_wbox()

        return self

    def __exit__(self, exc_type, exc_value, tb):
        # FIXME cache wbox or free resources
        self._wbox = None

    def _create_wbox(self):
        from .wavelet.cuda_backend import WaveletBox

        return WaveletBox(
            self.chunks_provider.chunk_size,
            time_step=1,
            scale_resolution=self.scale_resolution,
            omega0=self.omega0
        )

    @cached_property
    def complex_image(self):
        chunks = self.chunks_provider.get_chunks()
        return self.get_complex_image(chunks, decimate=self.decimate)

    def get_complex_image(self, chunks, decimate):
        if not self._wbox:
            raise RuntimeError('You need to use {} in a with block'.
                               format(self.__class__.__name__))

        return self._wbox.apply_cwt(chunks, decimate=decimate)

    def get_image(self, norma_window_len=None):
        abs_image = np.abs(self.complex_image)

        if norma_window_len:
            nolmalize_horizontal_smooth(abs_image, norma_window_len)

        return toimage(apply_colormap(abs_image))

    def get_spectrogram(self, norma_window_len=None):
        image = self.get_image(norma_window_len)

        return Spectrogram(image, self.chunks_provider)


class Spectrogram(object):
    def __init__(self, image, src):
        self.image = image
        self.src = src

    def x2time(self, x):
        raise NotImplemented

    def y2freq(self, y):
        raise NotImplemented


class CompositionWithProgressbar(Composition):
    def __init__(self, progressbar, *args, **kwargs):
        self.progressbar = progressbar
        super().__init__(*args, **kwargs)

    def get_complex_image(self, chunks, decimate):
        with self.progressbar(chunks) as chunks_:
            return super().get_complex_image(chunks_, decimate)
