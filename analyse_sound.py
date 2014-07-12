# -*- coding: utf-8 -*-
import os
from itertools import imap, repeat, takewhile

import click
import numpy as np
from click import echo
from matplotlib.colors import LinearSegmentedColormap
from pysoundfile import SoundFile
from scipy.misc import toimage

from wavelet_analyse.cuda_backend import WaveletBox


PROGRESSBAR_DEFAULTS = dict(
    width=0,
    show_percent=False,
    fill_char=click.style('#', fg='magenta')
)


@click.command()
@click.argument('source_sound_file', type=click.Path(exists=True))
@click.option('--norma_window_len', type=int, default=301)
def main(source_sound_file, norma_window_len):
    sound_file = SoundFile(source_sound_file)
    bitrate = sound_file.sample_rate

    file_dir, file_name = os.path.split(source_sound_file)
    sound_name, ext = os.path.splitext(file_name)

    # Make nsamples as power of two. More than one second
    nsamples = 2 ** (1 + int(np.log2(bitrate - 1)))

    decimation_factor = 7
    decimate = nsamples / 2 ** decimation_factor

    echo('Bitrate: {}'.format(bitrate))
    echo('Sound samples: {}'.format(sound_file.frames))
    echo('Fragment samples: {}'.format(nsamples))

    norma_window_len += 1 - (norma_window_len % 2)
    echo(u'Norma window len: {}'.format(norma_window_len))

    chunks_count = (sound_file.frames - 1) / (nsamples / 2) + 1
    echo(u'Chunks count: {}'.format(chunks_count))

    wav_chunks = imap(one_channel,
                      chunk_sound_file(sound_file, nsamples / 2))

    wbox = WaveletBox(nsamples, time_step=1,
                      scale_resolution=1 / 24., omega0=40)

    with click.progressbar(wav_chunks,
                           length=chunks_count,
                           **PROGRESSBAR_DEFAULTS) as chunks:
        whole_image = wbox.apply_cwt(chunks, decimate=decimate)

    abs_image = np.abs(whole_image)

    nolmalize_horizontal_smooth(abs_image, norma_window_len)
    mapped_image = apply_colormap(abs_image)
    img = toimage(mapped_image)
    whole_image_file_name = '{}.jpg'.format(sound_name)
    whole_image_file = os.path.join('.', whole_image_file_name)
    img.save(whole_image_file)


def one_channel(wav, channel_num=0):
    return wav[:, channel_num]


def chunk_sound_file(sound_file, size):
    return takewhile(len, imap(sound_file.read, repeat(size)))


def apply_colormap(image):
    return 255 * cmap(image)[:, :, :3]


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
        raise ValueError('window_len must be odd')

    if x.ndim != 1:
        raise ValueError('smooth only accepts 1 dimension arrays')

    if x.size < window_len:
        raise ValueError('Input vector needs to be bigger than window size')

    if window_len < 3:
        return x

    allowed = ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']

    if window not in allowed:
        raise ValueError('Window is on of %s' % allowed)

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
