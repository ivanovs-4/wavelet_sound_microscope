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

    def get_fragment(self, time_band, frequency_band=(None, None)):
        begin, end = tuple(sorted(time_band))

        fband = FrequenciesBand(*frequency_band)

        fragment_samples = self.samples[self.time2x(begin): self.time2x(end)]

        return SoundFragment(
            fragment_samples, self.samplerate, begin, fband
        )


class FrequenciesBand(object):
    def __init__(self, lower, upper):
        if lower is not None and upper is not None:
            self.lower, self.upper = sorted([lower, upper])

        else:
            self.lower, self.upper = lower, upper

    def filter(self, samples, samplerate):
        return bandpass_filter(samples, samplerate, self.lower, self.upper)


def bandpass_filter(samples, samplerate, f_lower=None, f_upper=None):
    flen = (samplerate // 16) * 2 + 1

    if f_lower is not None:
        lowpass = scipy.signal.firwin(
            flen, cutoff=f_lower/(samplerate/2),
            window='hanning'
        )

    else:
        lowpass = None

    if f_upper is not None:
        highpass = - scipy.signal.firwin(
            flen, cutoff=f_upper/(samplerate/2),
            window='hanning'
        )
        highpass[flen//2] = highpass[flen//2] + 1

    else:
        highpass = None

    if lowpass is not None:
        if highpass is not None:
            bandpass = lowpass + highpass
        else:
            bandpass = lowpass
    else:
        bandpass = highpass

    if bandpass is None:
        return samples

    bandpass = - bandpass
    bandpass[flen//2] = bandpass[flen//2] + 1

    return scipy.signal.lfilter(bandpass, 1, samples)


class SoundFragment(Sound):
    def __init__(self, samples, samplerate, begin, fband):
        if fband.lower is None and fband.upper is None:
            self.full_band_sound = self

        else:
            self.full_band_sound = SoundFragment(
                samples, samplerate, begin, FrequenciesBand(None, None)
            )

        self.samples = fband.filter(samples, samplerate)
        self.size = len(self.samples)
        self.samplerate = samplerate
        self.begin = begin
        self.duration = self.size / self.samplerate
        self.end = self.begin + self.duration

        self.fband = fband

    def get_fragment(self, *args, **kwargs):
        raise NotImplemented

    def __repr__(self):
        template = ('<%s size: %r, samplerate: %r, begin: %r, end: %r, '
                    'duration: %r, f:[%r:%r]>')

        return template % (
            self.__class__.__name__,
            self.size,
            self.samplerate,
            round_significant(self.begin, 2),
            round_significant(self.end, 2),
            round_significant(self.duration, 2),
            self.fband.lower and round_significant(self.fband.lower, 2),
            self.fband.upper and round_significant(self.fband.upper, 2),
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

    def get_blocks(self, block_size):
        # self.blocks_count = (sound_file.frames - 1) // (block_size // 2) + 1
        blocks = sf.blocks(self._filename, block_size)

        blocks = list(map(one_channel, blocks))
        blocks_count = len(blocks)

        return IterableWithLength(blocks, blocks_count)


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

    def get_blocks(self, block_size):
        iter_samples = iter(self.samples)
        iblocks = map(lambda _: list(it.islice(iter_samples, block_size)),
                      it.count())

        blocks = list(it.takewhile(len, iblocks))
        blocks_count = len(blocks)

        return IterableWithLength(blocks, blocks_count)
