import logging

import numpy as np
from scipy.misc import toimage

from .media import apply_colormap
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

    def get_spectrogram(self):
        return Spectrogram(
            abs_image=np.abs(self.complex_image),
            src=self.sound,
            scales=self._wbox.scales[:]
        )


class Spectrogram(object):
    def __init__(self, abs_image, src, scales):
        self.abs_image = abs_image
        self.image = toimage(apply_colormap(self.abs_image))
        self.width, self.height = self.image.size
        self.src = src
        self.scales = scales

    def x2time(self, x):
        return x * self.src.duration / self.width

    def y2freq(self, y):
        return np.interp(
            [self.height - y],
            np.linspace(0, self.height - 1, len(self.scales)),
            self.scales
        )[0]


class CompositionWithProgressbar(Composition):
    def __init__(self, progressbar, *args, **kwargs):
        self.progressbar = progressbar
        super().__init__(*args, **kwargs)

    def get_complex_image(self, chunks):
        with self.progressbar(chunks) as chunks_:
            return super().get_complex_image(chunks_)
