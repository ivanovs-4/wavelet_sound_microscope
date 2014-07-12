from functools import partial
from itertools import chain, imap, izip, tee

import numpy as np

PI2 = 2 * np.pi


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


def is_power_of_two(val):
    return val and val & (val - 1) == 0


class BaseWaveletBox(object):
    def __init__(self, nsamples, time_step, scale_resolution, omega0):
        if not is_power_of_two(nsamples):
            raise Exception(u'nsamples must be power of two')

        self.nsamples = nsamples
        self.scales = autoscales(nsamples, time_step,
                                 scale_resolution, omega0)
        self.angular_frequencies = angularfreq(nsamples, time_step)

    def apply_cwt(self, chunks, **kwargs):
        half_nsamples = self.nsamples / 2
        pad_num = 0

        def np_pad_right(data):
            pad_num = half_nsamples - len(data)
            if pad_num < 0:
                raise Exception(u'Chunks size must be equal to nsamples / 2'
                                u' except last, which may be shorter')
            if pad_num:
                return np.pad(data, (0, pad_num), 'constant')
            else:
                return data

        equal_sized_pieces = imap(np_pad_right, chunks)

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

        # Cut pad_num from last
        flattened_images[-1] = flattened_images[-1][:, :-pad_num]

        return np.concatenate(flattened_images, axis=1)


def angularfreq(nsamples, time_step):
    """ Compute angular frequencies """

    N2 = nsamples / 2.0

    return np.fromiter(
        (
            PI2 * (i if i <= N2 else i - nsamples) / (nsamples * time_step)
            for i in range(nsamples)
        ),
        np.float32, nsamples
    )


def autoscales(nsamples, time_step, scale_resolution, omega0):
    """ Compute scales as fractional power of two """

    s0 = (time_step * (omega0 + np.sqrt(2 + omega0 ** 2))) / PI2

    J = int(np.floor(scale_resolution ** -1 *
                        np.log2((nsamples * time_step) / s0)))

    return np.fromiter(
        (s0 * 2 ** (i * scale_resolution) for i in range(J + 1)),
        np.float32, J + 1
    )
