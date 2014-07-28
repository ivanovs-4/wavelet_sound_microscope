import logging
from contextlib import contextmanager

import numpy as np
from pysoundfile import SoundFile
from scipy.misc import toimage

from media import trinagle_colormap, apply_colormap, wav_chunks_from_sound_file
from wavelet_analyse.cuda_backend import WaveletBox


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def lazy_property(fn):
    return fn


@contextmanager
def statusbar(val):
    log.debug('info before %s', val)
    yield
    log.debug('info after %s', val)


class DummyProgressbar(object):
    def __init__(self, iterable, length=None, label=None):
        self.iterable = iterable

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        pass

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.iterable)


class Composition(object):
    def __init__(self, filename, statusbar_=None, progressbar_=None):
        self.statusbar = statusbar_ or statusbar
        self.progressbar = progressbar_ or DummyProgressbar

        self.filename = filename
        self.sound_file = SoundFile(self.filename)

        self.nsamples = 2 ** (
            1 + int(np.log2(self.sound_file.sample_rate - 1))
        )

        self.decimation_factor = 7
        self.decimate = nsamples / 2 ** decimation_factor

        log.debug('Bitrate: {}'.format(self.sound_file.sample_rate))
        log.debug('Sound samples: {}'.format(self.sound_file.frames))
        log.debug('Fragment samples: {}'.format(self.nsamples))

        self.norma_window_len = 301
        log.debug(u'Norma window len: {}'.format(self.norma_window_len))

    @lazy_property
    def wbox(self):
        with self.statusbar('Calculating WaveletBox...'):
            return WaveletBox(nsamples, time_step=1,
                              scale_resolution=1 / 24., omega0=40)

    @lazy_property
    def image(self):
        return toimage(apply_colormap(np.abs(self.whole_image)))

    @lazy_property
    def phase_image(self):
        return toimage(apply_colormap(np.angle(self.whole_image),
                                      trinagle_colormap))

    @lazy_property
    def whole_image(self):
        wav_chunks = wav_chunks_from_sound_file(self.sound_file,
                                                self.nsamples / 2)

        chunks_count = \
            (self.sound_file.frames - 1) / (self.nsamples / 2) + 1

        log.debug(u'Chunks count: {}'.format(chunks_count))

        with self.progressbar(wav_chunks, length=chunks_count,
                              label='Calculating wavelet transformation...'
                              ) as chunks:
            return self.wbox.apply_cwt(chunks, decimate=decimate)
