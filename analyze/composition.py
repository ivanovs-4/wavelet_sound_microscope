import logging

import numpy as np
from pysoundfile import SoundFile
from scipy.misc import toimage

from .media import apply_colormap, wav_chunks_from_sound_file, nolmalize_horizontal_smooth
from .wavelet.cuda_backend import WaveletBox
from utils import cached_property, IterableWithLength


log = logging.getLogger(__name__)


class ChunksProvider(object):
    def get_chunks(self):
        raise NotImplemented

    def chunk_size(self):
        raise NotImplemented


class ChunksProviderFromSoundFile(ChunksProvider):
    def __init__(self, filename):
        self.filename = filename

        self.sound_file = SoundFile(self.filename)

        self.chunk_size = 2 ** (
            1 + int(np.log2(self.sound_file.sample_rate - 1))
        )

        self.chunks_count = (self.sound_file.frames - 1) // (self.chunk_size // 2) + 1

        log.debug('Bitrate: %s', self.sound_file.sample_rate)
        log.debug('Sound samples: %s', self.sound_file.frames)
        log.debug('Chunk size: %s', self.chunk_size)
        log.debug('Chunks count: %s', self.chunks_count)

    def get_chunks(self):
        return IterableWithLength(self._get_chunks(), self.chunks_count)

    def _get_chunks(self):
        return wav_chunks_from_sound_file(self.sound_file, self.chunk_size // 2)


class Composition(object):
    def __init__(self, chunks_provider,
                 scale_resolution=1/36, omega0=70, decimation_factor=9):
        self.chunks_provider = chunks_provider
        self.scale_resolution = scale_resolution
        self.omega0 = omega0
        self.decimate = self.chunks_provider.chunk_size // 2 ** decimation_factor

        self.norma_window_len = 501
        log.debug('Norma window len: %s', self.norma_window_len)

    def prepare_wbox(self):
        return self.wbox

    @cached_property
    def wbox(self):
        return WaveletBox(
            self.chunks_provider.chunk_size,
            time_step=1,
            scale_resolution=self.scale_resolution,
            omega0=self.omega0
        )

    @cached_property
    def complex_image(self):
        return self.get_complex_image(self.chunks_provider.get_chunks(),
                                      decimate=self.decimate)

    def get_complex_image(self, chunks, decimate):
        return self.wbox.apply_cwt(chunks, decimate=decimate)

    def get_image(self, norma_window_len=None):
        abs_image = np.abs(self.complex_image)

        if norma_window_len:
            nolmalize_horizontal_smooth(abs_image, norma_window_len)

        return toimage(apply_colormap(abs_image))


class CompositionWithProgressbar(Composition):
    def __init__(self, progressbar, *args, **kwargs):
        self.progressbar = progressbar
        super().__init__(*args, **kwargs)

    def get_complex_image(self, chunks, decimate):
        with self.progressbar(chunks) as chunks_:
            return super().get_complex_image(chunks_, decimate)
