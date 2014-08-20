#!/usr/bin/env python3
import logging
import os

import click

from composition import Composition


logging.basicConfig()
logging.getLogger('').setLevel(logging.DEBUG)

log = logging.getLogger(__name__)


class CompositionWithProgressbar(Composition):
    def get_whole_image(self, chunks, decimate):
        with click.progressbar(chunks,
                               label='Calculating wavelet transformation',
                               fill_char=click.style('#', fg='magenta'),
                               ) as chunks_:
            return super(CompositionWithProgressbar, self). \
                get_whole_image(chunks_, decimate)


@click.command()
@click.argument('source_sound_file', type=click.Path(exists=True))
@click.option('--norma_window_len', type=int, default=301)
def main(source_sound_file, norma_window_len):
    composition = CompositionWithProgressbar(source_sound_file)

    img = composition.get_image(norma_window_len=norma_window_len)

    file_dir, file_name = os.path.split(source_sound_file)
    sound_name, ext = os.path.splitext(file_name)

    whole_image_file_name = '{}.jpg'.format(sound_name)
    whole_image_file = os.path.join('.', whole_image_file_name)

    img.save(whole_image_file)


if __name__ == '__main__':
    main()
