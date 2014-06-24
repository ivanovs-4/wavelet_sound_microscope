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


def gen_pieces(sf, nsamples):
    wav = sf.read(nsamples)

    while len(wav):
        yield np.pad(wav[:, 0], (0, nsamples - len(wav)), 'constant')
        wav = sf.read(nsamples)


def normalize_image(m):
    norma = np.max(np.abs(m))

    if norma == 0 or norma == float('inf'):
        return m

    return m / norma


cmap = LinearSegmentedColormap.from_list(
    'lightfire',
    sorted([
        (1, (1, 1, 1)),
        (0.6, (1, .6, 0)),
        (0.4, (.8, .2, .2)),
        (0.1, (.5, .2, .2)),
        (0, (0, 0, 0)),
    ])
)

def apply_colormap(image):
    return 255 * cmap(image)[:, :, :3]


@click.command()
@click.argument('source_sound_file', type=click.Path(exists=True))
def main(source_sound_file):
    sf = SoundFile(source_sound_file)
    bitrate = sf.sample_rate

    file_dir, file_name = os.path.split(source_sound_file)
    sound_name, ext = os.path.splitext(file_name)

    results_path = os.path.abspath(os.path.join('.', sound_name))
    shutil.rmtree(results_path, ignore_errors=True)
    os.mkdir(results_path)

    # Make nsamples as power of two. More than one second
    nsamples = 2**(1 + int(np.log2(bitrate - 1)))

    echo('Bitrate: {}'.format(bitrate))
    echo('N samples: {}'.format(nsamples))

    wbox = WaveletBox(nsamples, time_step=1, scale_resolution=1/24., omega0=40)

    ipieces = gen_pieces(sf, nsamples)

    for j, sample in enumerate(ipieces, 1):
        compex_image = wbox.cwt(sample, decimate=nsamples / 128)

        abs_image = np.abs(compex_image)

        normal_image = normalize_image(abs_image)

        mapped_image = apply_colormap(normal_image)

        img = toimage(mapped_image)

        image_file_name = '{:03d}_{}.png'.format(j, sound_name)
        echo(image_file_name)

        image_file = os.path.join(results_path, image_file_name)

        img.save(image_file)

# can montage results with command:
# $montage +frame +shadow +label -tile x1 -geometry +0+0 sample/* /tmp/g.jpg


if __name__ == '__main__':
    main()
