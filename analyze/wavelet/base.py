from functools import partial
from itertools import chain, tee
import logging

import numpy as np

log = logging.getLogger(__name__)


PI2 = 2 * np.pi


def pairwise(iterable):
    one, two = tee(iterable)
    next(two, None)
    return zip(one, two)


def grouper(iterable, n):
    return zip(*([iter(iterable)] * n))


def test_split_vertical():
    i, j = split_vertical([[1, 2], [3, 4]])
    assert i.tolist() == [[1], [3]]
    assert j.tolist() == [[2], [4]]


def split_vertical(mat):
    mat = np.asarray(mat)
    half = mat.shape[1] / 2
    return mat[:, :half], mat[:, half:]


def test_iconcatenate_pairs():
    pairs = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    assert [list(r) for r in iconcatenate_pairs(pairs)] == \
        [
            [1, 2, 3, 4, 5, 6],
            [4, 5, 6, 7, 8, 9],
    ]


def iconcatenate_pairs(items):
    for pair in pairwise(items):
        yield np.concatenate(pair)


def is_power_of_two(val):
    return val and val & (val - 1) == 0


def gen_halfs(arrays, size):
    halfsize = size // 2

    for array in arrays:
        pair = split_array(array, halfsize)

        for j in filter(len, pair):
            yield j


def test_gen_halfs():
    d = [ [1,2,3,4], [5,6,7], ]

    assert list(gen_halfs(d, 4)) == [[1, 2], [3, 4], [5, 6], [7]]


def split_array(array, where):
    return array[:where], array[where:]


def map_only_last(fn, iterable):
    items = iter(iterable)
    last = next(items)

    for elem in items:
        yield last
        last = elem

    yield fn(last)


def test_map_only_last():
    mapped = map_only_last(lambda x: x+1, range(3))

    assert list(mapped) == [0, 1, 3]


class NumpyPadder(object):
    def __init__(self, size):
        self.size = size

    def __call__(self, array):
        self.original_size = len(array)
        self.pad_size = self.size - self.original_size

        if self.pad_size == 0:
            return array

        elif self.pad_size > 0:
            return np.pad(array, (0, self.pad_size), 'constant')

        assert False  # Should never come here
        raise Exception('Pad size < 0')


class BaseWaveletBox(object):
    def __init__(self, nsamples, samplerate, scale_resolution, omega0):
        if not is_power_of_two(nsamples):
            raise Exception(u'nsamples must be power of two')

        self.nsamples = nsamples
        self.omega0 = omega0
        self.scales = autoscales(nsamples, samplerate,
                                 scale_resolution, omega0)
        self.angular_frequencies = angularfreq(nsamples, samplerate)

    @property
    def frequencies(self):
        # Set coefficient in accordance with wavelet type
        return 11 * (self.omega0 / 70) / self.scales

    def sound_apply_cwt(self, sound, progressbar, **kwargs):
        blocks = sound.get_blocks(self.nsamples)
        # blocks = sound.get_blocks(self.nsamples//2)

        with progressbar(blocks) as blocks_:
            return self._apply_cwt(blocks_, progressbar, **kwargs)

    def _apply_cwt(self, blocks, progressbar, decimate, **kwargs):
        half_nsamples = self.nsamples // 2

        chunks = gen_halfs(blocks, self.nsamples)

        padder = NumpyPadder(half_nsamples)

        equal_sized_pieces = map_only_last(padder, chunks)

        zero_pad = np.zeros(half_nsamples)
        overlapped_blocks = iconcatenate_pairs(
            chain([zero_pad], equal_sized_pieces, [zero_pad])
        )

        hanning = np.hanning(self.nsamples)
        windowed_pieces = map(lambda p: p * hanning, overlapped_blocks)

        complex_images = [
            self.cwt(windowed_piece, decimate, **kwargs)
            for windowed_piece in windowed_pieces
        ]

        halfs = chain.from_iterable(map(split_vertical, complex_images))
        next(halfs)
        overlapped_halfs = [left + right for left, right in grouper(halfs, 2)]

        # Cut pad size from last
        last_image_size = padder.original_size // decimate
        overlapped_halfs[-1] = overlapped_halfs[-1][:, :last_image_size]

        return np.concatenate(overlapped_halfs, axis=1)


def angularfreq(nsamples, samplerate):
    """ Compute angular frequencies """

    angfreq = np.arange(nsamples, dtype=np.float32)
    angfreq[-nsamples/2 + 1:] -= nsamples
    angfreq *= samplerate * PI2 / nsamples

    return angfreq


# Чем больше, тем больше октав снизу будет отброшено
LOWER_FQ_LIMIT_COEFF = 0.5


def autoscales(samples_count, samplerate, scale_resolution, omega0):
    """ Compute scales as fractional power of two """

    # morle_samples - количество отсчетов для базового вейвлета
    morle_samples = (omega0 + np.sqrt(2 + omega0 ** 2)) / PI2

    # scale - измеряется в секундах
    minimal_scale = morle_samples / samplerate

    # сколько базовых вейвлетов поместится (диапазон частот)
    freq_interval = samples_count / morle_samples

    skip_n_lower_octaves = LOWER_FQ_LIMIT_COEFF * samples_count / samplerate
    skipped_low_freq_interval = max(1, 2**skip_n_lower_octaves)

    visible_freq_interval = freq_interval / skipped_low_freq_interval
    maximal_scale = np.log2(visible_freq_interval)

    indexes_count = int(np.floor(maximal_scale / scale_resolution))

    indexes = np.arange(indexes_count + 1, dtype=np.float32)
    logarithmic_indexes = 2 ** (indexes * scale_resolution)

    return minimal_scale * logarithmic_indexes
