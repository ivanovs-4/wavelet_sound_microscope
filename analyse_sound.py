#!/usr/bin/env python3
import logging
import os
from functools import partial

import click

from composition import Composition


logging.basicConfig()


progressbar = partial(
    click.progressbar,
    fill_char=click.style('#', fg='magenta')
)


@click.command()
@click.argument('source_sound_file', type=click.Path(exists=True))
@click.option('--norma_window_len', type=int, default=301)
def main(source_sound_file, norma_window_len):
    composition = Composition(source_sound_file, progressbar=progressbar)

    img = composition.get_image(norma_window_len=norma_window_len)

    file_dir, file_name = os.path.split(source_sound_file)
    sound_name, ext = os.path.splitext(file_name)

    whole_image_file_name = '{}.jpg'.format(sound_name)
    whole_image_file = os.path.join('.', whole_image_file_name)

    img.save(whole_image_file)


if __name__ == '__main__':
    main()
