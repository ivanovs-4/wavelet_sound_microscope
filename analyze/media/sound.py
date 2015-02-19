import logging
from itertools import repeat, takewhile

import numpy as np
from pysoundfile import SoundFile

from utils import IterableWithLength


log = logging.getLogger(__name__)


class Sound(object):
    pass


class SoundFromSoundFile(Sound):
    def __init__(self, filename):
        self.filename = filename
        self.sound_file = SoundFile(self.filename)
        self.samplerate = self.sound_file.samplerate

    def get_chunks(self, chunk_size):
        # self.chunks_count = (sound_file.frames - 1) // (chunk_size // 2) + 1
        # FIXME chunk_size or half
        blocks = self.sound_file.blocks(chunk_size // 2)

        def one_channel(wav, channel_num=0):
            return wav[:, channel_num]

        chunks = list(map(one_channel, blocks))
        chunks_count = len(chunks)

        return IterableWithLength(chunks, chunks_count)
