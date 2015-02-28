import itertools as it
import logging
import subprocess as sub

import numpy as np
import scipy.signal
import pysoundfile as sf

from utils import IterableWithLength, round_significant


log = logging.getLogger(__name__)


class Sound(object):
    # All ancessors should implement following attributes:
    duration = 0
    samplerate = 1
    size = 0
    samples = []

    def x2time(self, x):
        return x * self.duration / self.size

    def time2x(self, time):
        """
        time = x * self.duration / self.size
        x * self.duration = time * self.size
        x = time * self.size / self.duration
        """
        return int(time * self.size / self.duration)

    def play(self):
        log.debug('Play %r', self)

        # FIXME change adhoc play to universal
        fragment_filename = '/tmp/fragment.wav'
        sub.check_call(['rm', '-rf', fragment_filename])
        sf.write(self.samples, fragment_filename, self.samplerate)
        sub.check_call(['mplayer', '-ao', 'alsa:noblock:device=hw=Set',
                        fragment_filename])

    def get_fragment(self, time_band, frequency_band=None):
        begin, end = tuple(sorted(time_band))

        if frequency_band:
            f_lower, f_upper = tuple(sorted(frequency_band))
        else:
            f_lower, f_upper = None, None

        fragment_samples = SoundFragment.calculate_samples(
            self.samples, self.samplerate,
            self.time2x(begin), self.time2x(end),
            f_lower, f_upper
        )

        return SoundFragment(
            fragment_samples, self.samplerate, begin, f_lower, f_upper
        )


class SoundFragment(Sound):
    def __init__(self, samples, samplerate, begin, f_lower, f_upper):
        self.samples = samples
        self.size = len(samples)
        self.samplerate = samplerate
        self.begin = begin
        self.duration = self.size / self.samplerate
        self.end = self.begin + self.duration

        self.f_lower = f_lower
        self.f_upper = f_upper

    @staticmethod
    def calculate_samples(src_samples, samplerate, s_from, s_to,
                          f_lower, f_upper):

        # FIXME implement frequency filter if f_lower, f_upper
        return src_samples[s_from: s_to + 1]

    def __repr__(self):
        template = ('<%s size: %r, samplerate: %r, begin: %r, end: %r, '
                    'duration: %r, f_lower: %r, f_upper: %r>')

        return template % (
            self.__class__.__name__,
            self.size,
            self.samplerate,
            round_significant(self.begin, 2),
            round_significant(self.end, 2),
            round_significant(self.duration, 2),
            round_significant(self.f_lower, 2),
            round_significant(self.f_upper, 2),
        )


def one_channel(wav, channel_num=0):
    return wav[:, channel_num]


class SoundFromSoundFile(Sound):
    def __init__(self, filename):
        self._filename = filename

        with sf.SoundFile(self._filename) as sound_file:
            self.samplerate = sound_file.samplerate
            self.size = len(sound_file)

        self.duration = self.size / self.samplerate

        log.debug('Soundfile samplerate: %r size: %r duration: %r',
                  self.samplerate, self.size, self.duration)

    @property
    def samples(self):
        _samples, frequency = sf.read(self._filename)

        return one_channel(_samples, 0)

    def get_chunks(self, chunk_size):
        # self.chunks_count = (sound_file.frames - 1) // (chunk_size // 2) + 1
        # FIXME chunk_size or half
        blocks = sf.blocks(self._filename, chunk_size)

        chunks = list(map(one_channel, blocks))
        chunks_count = len(chunks)

        return IterableWithLength(chunks, chunks_count)


class SoundResampled(Sound):
    def __init__(self, original, samplerate):
        self.samplerate = samplerate
        self.size = int(original.size * samplerate / original.samplerate)
        self.samples = scipy.signal.resample(original.samples, self.size)
        self.duration = original.duration

        # debug
        cut_duration = 40
        if self.duration > cut_duration:
            self.size = cut_duration * self.samplerate
            self.samples = self.samples[:self.size]
            self.duration = self.size / self.samplerate

    def get_chunks(self, chunk_size):
        iter_samples = iter(self.samples)
        ichunks = map(lambda _: list(it.islice(iter_samples, chunk_size)),
                      it.count())

        chunks = list(it.takewhile(len, ichunks))
        chunks_count = len(chunks)

        return IterableWithLength(chunks, chunks_count)
