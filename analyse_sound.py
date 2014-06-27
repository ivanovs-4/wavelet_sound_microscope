# -*- coding: utf-8 -*-
import os
import sys

import click
from click import echo
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from pysoundfile import SoundFile
from scipy.misc import toimage

from wavelet_analyse.cuda_backend import WaveletBox


def gen_pieces(sf, nsamples, overlap=0):
    gap = [0 for j in range(overlap / 2)]

    len_prev_readed = nsamples + 1

    while len_prev_readed >= nsamples - overlap:
        wav = sf.read(nsamples - len(gap))

        channel_wav = wav[:, 0]

        len_prev_readed = len(channel_wav)

        fragment = np.concatenate((gap, channel_wav), axis=0)

        fragment = np.pad(
            fragment,
            (0, nsamples - len(fragment)),
            'constant'
        )

        yield fragment

        gap = fragment[-overlap:]


def normalize_image(m):
    norma = np.max(np.abs(m))

    if norma == 0 or norma == float('inf'):
        return m

    return m / norma


cmap = LinearSegmentedColormap.from_list(
    'lightfire',
    sorted([
        (1, (1, 1, 1)),
        (0.6, (1, .8, .3)),
        (0.4, (.8, .7, .1)),
        (0.2, (.0, .4, .7)),
        (0.05, (.0, .0, .6)),
        (0, (0, 0, 0)),
    ])
)

def apply_colormap(image):
    return 255 * cmap(image)[:, :, :3]


@click.command()
@click.argument('source_sound_file', type=click.Path(exists=True))
@click.option('--overlap_factor', type=int, default=4)
@click.option('--norma_window_len', type=int, default=301)
def main(source_sound_file, overlap_factor, norma_window_len):
    sf = SoundFile(source_sound_file)
    bitrate = sf.sample_rate

    file_dir, file_name = os.path.split(source_sound_file)
    sound_name, ext = os.path.splitext(file_name)

    # Make nsamples as power of two. More than one second
    nsamples = 2**(1 + int(np.log2(bitrate - 1)))

    decimate = nsamples / 128

    echo('Bitrate: {}'.format(bitrate))
    echo('Sound samples: {}'.format(sf.frames))
    echo('Fragment samples: {}'.format(nsamples))
    echo('Overlap factor: {}'.format(overlap_factor))

    norma_window_len += 1 - (norma_window_len % 2)
    echo(u'Norma window len {}'.format(norma_window_len))

    wbox = WaveletBox(nsamples, time_step=1, scale_resolution=1/24., omega0=40)

    overlap = nsamples / overlap_factor

    decimated_half_overlap = overlap / decimate / 2

    ipieces = gen_pieces(sf, nsamples, overlap)

    pieces_count = ((sf.frames - 1) /
                    (nsamples - overlap)) + 1

    image_files = []

    slides = []

    with click.progressbar(
        ipieces,
        length=pieces_count,
        width=0,
        show_percent=False,
        label=u'Pieces count: {}'.format(pieces_count),
        fill_char=click.style('#', fg='magenta')
    ) as bar:
        for j, sample in enumerate(bar, 1):
            complex_image = wbox.cwt(sample, decimate=decimate)

            stripped_complex_image = complex_image[
                :, decimated_half_overlap: -decimated_half_overlap
            ]

            abs_image = np.abs(stripped_complex_image)

            slides.append(abs_image)

    whole_image = np.concatenate(slides, axis=1)
    nolmalize_horizontal_smooth(whole_image, norma_window_len)
    mapped_image = apply_colormap(whole_image)
    img = toimage(mapped_image)
    whole_image_file_name = '{}.jpg'.format(sound_name)
    whole_image_file = os.path.join('.', whole_image_file_name)
    img.save(whole_image_file)


def nolmalize_horizontal_smooth(arr, window_len):
    maxes = np.abs(arr).max(axis=0)

    smoothed = smooth(maxes, window_len)
    smoothed[smoothed == 0] = 1

    norma = smoothed * (maxes / smoothed).max()

    arr /= norma


def smooth(x, window_len=11, window='hanning'):
    """
    Smooth the data using a window with requested size

    This method is based on the convolution of a scaled window with the signal.
    The signal is prepared by introducing reflected copies of the signal
    (with the window size) in both ends so that transient parts are minimized
    in the begining and end part of the output signal.
    """

    if window_len % 2 != 1:
        raise ValueError, "window_len must be odd"

    if x.ndim != 1:
        raise ValueError, "smooth only accepts 1 dimension arrays"

    if x.size < window_len:
        raise ValueError, "Input vector needs to be bigger than window size"

    if window_len < 3:
        return x

    allowed = ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']

    if window not in allowed:
        raise ValueError, "Window is on of %s" % allowed

    s = np.r_[x[window_len - 1: 0: -1], x, x[-1: -window_len: -1]]

    if window == 'flat':  # moving average
        w = np.ones(window_len, 'd')

    else:
        w = eval('np.' + window + '(window_len)')

    y = np.convolve(w / w.sum(), s, mode='valid')

    return y[(window_len / 2): -(window_len / 2)]


def test_smooth():
    assert smooth(np.linspace(-4, 4, 100)).shape[0] == 100
    assert smooth(np.linspace(-4, 4, 101)).shape[0] == 101
    assert smooth(np.linspace(-4, 4, 100), 13).shape[0] == 100
    assert smooth(np.linspace(-4, 4, 101), 13).shape[0] == 101
    assert smooth(np.linspace(-4, 4, 1000), 131).shape[0] == 1000
    assert smooth(np.linspace(-4, 4, 1001), 131).shape[0] == 1001


if __name__ == '__main__':
    main()
