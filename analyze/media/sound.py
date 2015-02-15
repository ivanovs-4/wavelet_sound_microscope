import logging
from itertools import repeat, takewhile

import numpy as np
from pysoundfile import SoundFile

from utils import IterableWithLength


log = logging.getLogger(__name__)


class ChunksProvider(object):
    def __init__(self, chunks, chunk_size, chunks_count):
        self.chunks = chunks
        self.chunk_size = chunk_size
        self.chunks_count = chunks_count

        log.debug('Chunk size: %s', chunk_size)
        log.debug('Chunks count: %s', chunks_count)

    def get_chunks(self):
        return IterableWithLength(self.chunks, self.chunks_count)


class ChunksProviderFromSoundFile(ChunksProvider):
    def __init__(self, filename):
        self.filename = filename

        sound_file = SoundFile(self.filename)

        log.debug('Bitrate: %s', sound_file.samplerate)

        chunk_size = 2 ** (
            1 + int(np.log2(sound_file.samplerate - 1))
        )

        def one_channel(wav, channel_num=0):
            return wav[:, channel_num]

        # self.chunks_count = (sound_file.frames - 1) // (chunk_size // 2) + 1
        # FIXME chunk_size or half
        chunks = sound_file.blocks(chunk_size // 2)
        chunks = list(map(one_channel, chunks))

        super().__init__(chunks, chunk_size, len(chunks))
