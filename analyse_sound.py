# -*- coding: utf-8 -*-
import os
import shutil
import sys
from subprocess import check_call

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
@click.option('--montage', is_flag=True, default=False)
@click.option('--overlap_factor', type=int, default=8)
def main(source_sound_file, montage, overlap_factor):
    sf = SoundFile(source_sound_file)
    bitrate = sf.sample_rate

    file_dir, file_name = os.path.split(source_sound_file)
    sound_name, ext = os.path.splitext(file_name)

    results_path = os.path.abspath(os.path.join('.', sound_name))
    shutil.rmtree(results_path, ignore_errors=True)
    os.mkdir(results_path)

    # Make nsamples as power of two. More than one second
    nsamples = 2**(1 + int(np.log2(bitrate - 1)))

    decimate = nsamples / 128

    echo('Bitrate: {}'.format(bitrate))
    echo('Sound samples: {}'.format(sf.frames))
    echo('Fragment samples: {}'.format(nsamples))
    echo('Overlap factor: {}'.format(overlap_factor))

    wbox = WaveletBox(nsamples, time_step=1, scale_resolution=1/24., omega0=40)

    overlap = nsamples / overlap_factor

    decimated_half_overlap = overlap / decimate / 2

    ipieces = gen_pieces(sf, nsamples, overlap)

    pieces_count = ((sf.frames - 1) /
                    (nsamples - overlap)) + 1

    image_files = []

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

            normal_image = normalize_image(abs_image)

            mapped_image = apply_colormap(normal_image)

            img = toimage(mapped_image)

            image_file_name = '{:03d}_{}.png'.format(j, sound_name)

            image_file = os.path.join(results_path, image_file_name)

            img.save(image_file)

            image_files.append(image_file)

    if montage:
        full_image_file_name = '{}.jpg'.format(sound_name)

        full_image_file = os.path.join(results_path, full_image_file_name)

        check_call(
            'montage +frame +shadow +label -tile x1 -geometry +0+0'.split() +
            image_files + [full_image_file]
        )

        echo(u'Montaged: {}'.format(full_image_file))


if __name__ == '__main__':
    main()
