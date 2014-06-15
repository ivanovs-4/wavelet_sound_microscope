import os
import shutil
import sys
from subprocess import check_call

import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from pysoundfile import SoundFile

from wavelet_analyse.cuda_backend import WaveletBox


def gen_pieces(sf, n_samples):
    wav = sf.read(n_samples)

    while len(wav):
        yield np.pad(wav[:, 0], (0, n_samples - len(wav)), 'constant')
        wav = sf.read(n_samples)


def normalize_image(m):
    return m / np.max(np.abs(m))


def apply_colormap(image):
    return image * 255


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('soundfile')

    values = parser.parse_args()

    sf = SoundFile(values.soundfile)
    bitrate = sf.sample_rate

    file_dir, file_name = os.path.split(values.soundfile)
    sound_name, ext = os.path.splitext(file_name)

    results_path = os.path.abspath(os.path.join('.', sound_name))
    shutil.rmtree(results_path, ignore_errors=True)
    os.mkdir(results_path)

    # Make n_samples as power of two. More than one second
    n_samples = 2**(1 + int(np.log2(bitrate - 1)))

    print 'Bitrate:', bitrate
    print 'N samples:', n_samples

    wbox = WaveletBox(N=n_samples, dt=1, dj=1/24., p=40)

    ipieces = gen_pieces(sf, n_samples)

    for j, sample in enumerate(ipieces, 1):
        compex_image = wbox.cwt(sample, decimate=n_samples / 128)

        abs_image = np.abs(compex_image)

        normal_image = normalize_image(abs_image)

        mapped_image = apply_colormap(normal_image)

        img = Image.fromarray(mapped_image).convert('RGB')

        image_file_name = '{:03d}_{}.png'.format(j, sound_name)
        print image_file_name

        image_file = os.path.join(results_path, image_file_name)

        img.save(image_file)
