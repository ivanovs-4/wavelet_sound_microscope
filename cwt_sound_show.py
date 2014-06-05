import sys

import numpy as np
from scipy.ndimage import interpolation
import matplotlib.pyplot as plt
from scipy.io import wavfile

import wavelet_continuous as wave


bitrate, wav = wavfile.read('sample.wav')

SIZE = 64 * 2

y = wav[:bitrate * SIZE / 64, 0]

scales = wave.autoscales(N=y.shape[0], dt=100, dj=0.05, p=2)

compex_image = wave.cwt(y, dt=100, scales=scales, p=2)

abs_image = np.abs(compex_image)

image = interpolation.zoom(abs_image, (1, 1. / SIZE))

fig = plt.figure(1)

ax = plt.subplot(1,1,1)
p = ax.imshow(image)
p.set_cmap('copper')

fig.set_tight_layout(True)

plt.show()
