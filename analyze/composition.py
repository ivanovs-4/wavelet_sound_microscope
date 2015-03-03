import bisect
import logging

import numpy as np
from scipy.misc import toimage

from .media import apply_colormap
from utils import cached_property


log = logging.getLogger(__name__)


class Composition(object):
    def __init__(self, sound,
                 scale_resolution=1/36, omega0=70):
        self.sound = sound
        self.scale_resolution = scale_resolution
        self.omega0 = omega0

        # Calculate chunk_size
        # samplerate = sound.samples / sound.duration
        self.samplerate = sound.samplerate

        self.overlapping_block_size = 2 ** 17
        self.decimate = 2 ** int(np.log2(self.samplerate) - 8)

        self.chunk_size = self.overlapping_block_size // 2

        self._wbox = None

    def __enter__(self):
        from .wavelet.cuda_backend import WaveletBox

        self._wbox = WaveletBox(
            self.overlapping_block_size,
            samplerate=self.samplerate,
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
            sound=self.sound,
            scales=self._wbox.scales[:]
        )


class Spectrogram(object):
    def __init__(self, abs_image, sound, scales):
        self.abs_image = abs_image
        self.image = toimage(apply_colormap(self.abs_image))
        self.width, self.height = self.image.size
        self.sound = sound
        self.scales = scales

    def x2time(self, x):
        """
        Assume self.width and self.sound.size equal
        """
        return self.sound.x2time(x * self.sound.size / self.width)

    def time2x(self, time):
        """
        Assume self.width and self.sound.size equal
        """
        return int(self.sound.time2x(time) * self.width / self.sound.size)

    def y2freq(self, y):
        return np.interp(
            [self.height - y],
            np.linspace(0, self.height - 1, len(self.scales)),
            self.scales
        )[0]

    def freq2y(self, f):
        return self.height - bisect.bisect_left(self.scales, f)

    def get_sound_fragment(self, x1x2, y1y2):
        time_band = tuple(map(self.x2time, x1x2))
        frequency_band = tuple(map(self.y2freq, y1y2))

        return self.sound.get_fragment(time_band, frequency_band)


class CompositionWithProgressbar(Composition):
    def __init__(self, progressbar, *args, **kwargs):
        self.progressbar = progressbar
        super().__init__(*args, **kwargs)

    def get_complex_image(self, chunks):
        with self.progressbar(chunks) as chunks_:
            return super().get_complex_image(chunks_)
