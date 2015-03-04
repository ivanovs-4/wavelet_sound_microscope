from functools import partial
from itertools import chain, tee

import numpy as np

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


def gen_halfs(arrays):
    for array in arrays:
        pair = split_array(array, len(array) // 2)

        for j in filter(len, pair):
            yield j


def split_array(array, where):
    return array[:where], array[-where:]


class BaseWaveletBox(object):
    def __init__(self, nsamples, samplerate, scale_resolution, omega0):
        if not is_power_of_two(nsamples):
            raise Exception(u'nsamples must be power of two')

        self.nsamples = nsamples
        self.scales = autoscales(nsamples, samplerate,
                                 scale_resolution, omega0)
        self.angular_frequencies = angularfreq(nsamples, samplerate)

    def sound_apply_cwt(self, sound, progressbar, **kwargs):
        blocks = sound.get_blocks(self.nsamples)

        with progressbar(blocks) as blocks_:
            return self._apply_cwt(self, blocks_, progressbar, **kwargs)

    def _apply_cwt(self, blocks, **kwargs):
        chunks = gen_halfs(blocks)

        half_nsamples = self.nsamples / 2
        pad_num = 0

        def np_pad_right(data):
            pad_num = half_nsamples - len(data)
            if pad_num < 0:
                assert False  # Should never come here
                raise Exception(u'Chunks size must be equal to nsamples / 2'
                                u' except last, which may be shorter')
            if pad_num:
                return np.pad(data, (0, pad_num), 'constant')
            else:
                return data

        equal_sized_pieces = map(np_pad_right, chunks)

        zero_pad = np.zeros(half_nsamples)
        overlapped_pieces = iconcatenate_pairs(
            chain([zero_pad], equal_sized_pieces, [zero_pad])
        )

        hanning = np.hanning(self.nsamples)
        windowed_pieces = map(lambda p: p * hanning, overlapped_pieces)

        complex_images = [
            self.cwt(windowed_piece, **kwargs)
            for windowed_piece in windowed_pieces
        ]

        halfs = chain.from_iterable(map(split_vertical, complex_images))
        next(halfs)
        flattened_images = [left + right for left, right in grouper(halfs, 2)]

        # Cut pad_num from last
        flattened_images[-1] = flattened_images[-1][:, :-pad_num]

        return np.concatenate(flattened_images, axis=1)


def angularfreq(nsamples, samplerate):
    """ Compute angular frequencies """

    N2 = nsamples / 2.0

    return np.array(
        [
            samplerate * PI2 * (i if i <= N2 else i - nsamples) / nsamples
            for i in range(nsamples)
        ],
        np.float32
    )


def autoscales(samples_count, samplerate, scale_resolution, omega0):
    """ Compute scales as fractional power of two """

    samples_duration = samples_count / samplerate

    upper_frequency = PI2 * samples_count / (omega0 + np.sqrt(2 + omega0 ** 2))

    scales_count = int(np.floor(
        np.log2(upper_frequency) / scale_resolution
    ))

    indexes = np.arange(scales_count + 1, endpoint=False, dtype=np.float32)

    upper_frequency_scale = samples_duration / upper_frequency

    return upper_frequency_scale * (2 ** (indexes * scale_resolution))
