# -*- coding: utf-8 -*-
import os
from itertools import imap, repeat, takewhile

import click
import numpy as np
from click import echo
from pysoundfile import SoundFile
from scipy.misc import toimage

from media import (apply_colormap, nolmalize_horizontal_smooth,
                   wav_chunks_from_sound_file)
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

    wbox = WaveletBox(nsamples, time_step=1,
                      scale_resolution=1 / 24., omega0=40)

    with click.progressbar(wav_chunks_from_sound_file(sound_file, nsamples / 2),
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


if __name__ == '__main__':
    main()
