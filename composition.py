import logging
from contextlib import contextmanager

import numpy as np
from pysoundfile import SoundFile
from scipy.misc import toimage

from media import apply_colormap, wav_chunks_from_sound_file, nolmalize_horizontal_smooth
from utils import cached_property
from wavelet_analyse.cuda_backend import WaveletBox


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


@contextmanager
def statusbar_(val):
    # log.debug('Statusbar before %s', val)
    yield
    # log.debug('Statusbar after %s', val)


class DummyProgressbar(object):
    def __init__(self, iterable, length=None, label=None):
        self.iterable = iterable

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        pass

    def __iter__(self):
        return self.iterable

    def __next__(self):
        return next(self.iterable)


class Composition(object):
    def __init__(self, filename, statusbar=None, progressbar=None):
        self.statusbar = statusbar or statusbar_
        self.progressbar = progressbar or DummyProgressbar

        self.filename = filename
        self.sound_file = SoundFile(self.filename)

        self.nsamples = 2 ** (
            1 + int(np.log2(self.sound_file.sample_rate - 1))
        )

        self.decimation_factor = 7
        self.decimate = self.nsamples // 2 ** self.decimation_factor

        log.debug('Bitrate: {}'.format(self.sound_file.sample_rate))
        log.debug('Sound samples: {}'.format(self.sound_file.frames))
        log.debug('Fragment samples: {}'.format(self.nsamples))

        self.norma_window_len = 301
        log.debug(u'Norma window len: {}'.format(self.norma_window_len))

    @cached_property
    def wbox(self):
        with self.statusbar('Calculating WaveletBox'):
            return WaveletBox(self.nsamples, time_step=1,
                              scale_resolution=1 / 24., omega0=40)

    def get_image(self, norma_window_len=None):
        abs_image = np.abs(self.whole_image)

        if norma_window_len:
            nolmalize_horizontal_smooth(abs_image, norma_window_len)

        return toimage(apply_colormap(abs_image))

    @cached_property
    def whole_image(self):
        wav_chunks = wav_chunks_from_sound_file(self.sound_file,
                                                self.nsamples // 2)

        chunks_count = \
            (self.sound_file.frames - 1) // (self.nsamples // 2) + 1

        log.debug(u'Chunks count: {}'.format(chunks_count))

        with self.progressbar(wav_chunks, length=chunks_count,
                              label='Calculating wavelet transformation'
                              ) as chunks:
            return self.wbox.apply_cwt(chunks, decimate=self.decimate)
