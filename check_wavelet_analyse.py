import sys

import numpy as np
from scipy.ndimage import interpolation
import matplotlib.pyplot as plt
from scipy.io import wavfile

from wavelet_analyse import WaveletBox, BACKEND

print 'Backend:', BACKEND

fig = plt.figure(1)

bitrate, stereo_wav = wavfile.read('sample.wav')

wav = stereo_wav.transpose()[0]

n_samples = bitrate

wbox = WaveletBox(N=n_samples, dt=1, dj=1/12.)

n_images = (wav.shape[0] - 1) / n_samples + 1
padded_wav_size = n_images * n_samples

wav_pieces = np.pad(wav, (0, padded_wav_size - wav.shape[0]), 'constant') \
    .reshape((n_images, n_samples))


for j, y in enumerate(wav_pieces):
    compex_image = wbox.cwt(y)

    abs_image = np.abs(compex_image)

    image = interpolation.zoom(abs_image, (1, 1. * 50 / bitrate))

    ax = plt.subplot(1, n_images, j + 1)
    ax.set_xticklabels( () )
    ax.set_yticklabels( () )
    p = ax.imshow(image)
    p.set_cmap('copper')

fig.set_tight_layout(True)

plt.show()
