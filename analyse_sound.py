#!/usr/bin/env python3
import logging
import os
from contextlib import contextmanager

import click

from composition import Composition


logging.basicConfig()

log = logging.getLogger(__name__)


class CompositionWithProgressbar(Composition):
    def get_whole_image(self, chunks, decimate):
        with click.progressbar(chunks,
                               label='Calculating wavelet transformation',
                               fill_char=click.style('#', fg='magenta'),
                               ) as chunks_:
            return super().get_whole_image(chunks_, decimate)


@contextmanager
def statusbar(val):
    log.debug('Status before %s', val)
    yield
    log.debug('Status after %s', val)


@click.command()
@click.argument('source_sound_file', type=click.Path(exists=True))
@click.argument('destination_image_file', type=click.Path(), required=False)
@click.option('--norma_window_len', type=int, default=301)
@click.option('--verbose/--silent', default=False)
def main(source_sound_file, destination_image_file, norma_window_len, verbose):
    if verbose:
        logging.getLogger('').setLevel(logging.DEBUG)

    composition = CompositionWithProgressbar(source_sound_file)

    with statusbar('Prepare Wavelet Box'):
        composition.prepare_wbox()

    img = composition.get_image(norma_window_len=norma_window_len)

    file_dir, file_name = os.path.split(source_sound_file)
    sound_name, ext = os.path.splitext(file_name)

    if not destination_image_file:
        name = '{}.jpg'.format(sound_name)
        destination_image_file = os.path.join('.', name)

    img.save(destination_image_file)


if __name__ == '__main__':
    main()
