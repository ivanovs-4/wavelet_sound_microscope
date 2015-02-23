import logging

import numpy as np
from scipy.misc import toimage

from .media import apply_colormap, nolmalize_horizontal_smooth
from utils import cached_property


log = logging.getLogger(__name__)


class Composition(object):
    def __init__(self, sound,
                 scale_resolution=1/36, omega0=70, decimation_factor=9):
        self.sound = sound
        self.scale_resolution = scale_resolution
        self.omega0 = omega0

        # Calculate chunk_size
        # samplerate = sound.samples / sound.duration
        samplerate = sound.samplerate
        self.fragment_size = 2 ** (
            1 + int(np.log2(samplerate - 1))
        )
        self.chunk_size = self.fragment_size // 2

        self.decimate = self.fragment_size // 2 ** decimation_factor

        self.norma_window_len = 501
        log.debug('Norma window len: %s', self.norma_window_len)

        self._wbox = None

    def __enter__(self):
        from .wavelet.cuda_backend import WaveletBox

        self._wbox = WaveletBox(
            self.fragment_size,
            time_step=1,
            scale_resolution=self.scale_resolution,
            omega0=self.omega0
        )

        return self

    def __exit__(self, exc_type, exc_value, tb):
        # FIXME cache wbox or free resources
        self._wbox = None

    @cached_property
    def complex_image(self):
        chunks = self.sound.get_chunks(self.chunk_size)

        return self.get_complex_image(chunks)

    def get_complex_image(self, chunks):
        if not self._wbox:
            raise RuntimeError('You need to use {} in a with block'.
                               format(self.__class__.__name__))

        return self._wbox.apply_cwt(chunks, decimate=self.decimate)

    def get_image(self, norma_window_len=None):
        abs_image = np.abs(self.complex_image)

        if norma_window_len:
            nolmalize_horizontal_smooth(abs_image, norma_window_len)

        # FIXME move apply_colormap to Spectrogram
        return toimage(apply_colormap(abs_image))

    def get_spectrogram(self, norma_window_len=None):
        image = self.get_image(norma_window_len)

        return Spectrogram(
            image=image,
            src=self.sound,
            frequencies=self._wbox.angular_frequencies[:]
        )


class Spectrogram(object):
    def __init__(self, image, src, frequencies):
        self.image = image
        self.width, self.height = self.image.size
        self.src = src
        self.frequencies = frequencies

    def x2time(self, x):
        return x * self.src.duration / self.width

    def y2freq(self, y):
        return np.interp(
            [y],
            np.linspace(0, self.height - 1, len(self.frequencies)),
            self.frequencies
        )[0]


class CompositionWithProgressbar(Composition):
    def __init__(self, progressbar, *args, **kwargs):
        self.progressbar = progressbar
        super().__init__(*args, **kwargs)

    def get_complex_image(self, chunks):
        with self.progressbar(chunks) as chunks_:
            return super().get_complex_image(chunks_)
