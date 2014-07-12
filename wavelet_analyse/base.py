from functools import partial
from itertools import chain, imap, izip, tee

import numpy as np


def pairwise(iterable):
    one, two = tee(iterable)
    next(two, None)
    return izip(one, two)


def grouper(iterable, n):
    return izip(*([iter(iterable)] * n))


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


def np_pad_right(data, size, fillvalue):
    return np.pad(data, (fillvalue, size - len(data)), 'constant')


def is_power_of_two(val):
    return val and val & (val - 1) == 0


class BaseWaveletBox(object):

    def __init__(self, nsamples, time_step, scale_resolution, omega0):
        if not is_power_of_two(nsamples):
            raise Exception(u'nsamples must be power of two')

    def apply_wbox_cwt(self, chunks, **kwargs):
        half_nsamples = self.nsamples / 2

        equal_sized_pieces = imap(
            partial(np_pad_right, size=half_nsamples, fillvalue=0),
            chunks
        )

        zero_pad = np.zeros(half_nsamples)
        overlapped_pieces = iconcatenate_pairs(
            chain([zero_pad], equal_sized_pieces, [zero_pad])
        )

        hanning = np.hanning(self.nsamples)
        windowed_pieces = imap(lambda p: p * hanning, overlapped_pieces)

        complex_images = [
            self.cwt(windowed_piece, **kwargs)
            for windowed_piece in windowed_pieces
        ]

        halfs = chain.from_iterable(imap(split_vertical, complex_images))
        next(halfs)
        flattened_images = map(lambda r_u: r_u[0] + r_u[1], grouper(halfs, 2))

        return np.concatenate(flattened_images, axis=1)
