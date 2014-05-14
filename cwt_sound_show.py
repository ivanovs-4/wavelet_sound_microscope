import sys

import numpy as np
from scipy.ndimage import interpolation
import matplotlib.pyplot as plt
from scipy.io import wavfile

import wavelet_continuous as wave


bitrate, wav = wavfile.read('sample.wav')

SIZE = 64 * 1

y = wav[:bitrate * SIZE / 64, 0]

scales = wave.autoscales(N=y.shape[0], dt=100, dj=0.05, wf='morlet', p=2)
compex_image = wave.cwt(y, dt=100, scales=scales, wf='morlet', p=2)

# image = np.abs(compex_image)
image = interpolation.zoom(np.abs(compex_image), (1, 1. / SIZE))

fig = plt.figure(1)

ax = plt.subplot(2,1,1)
p = ax.imshow(image)
p.set_cmap('copper')
# ax.autoscale_view(tight=True)

fig.set_tight_layout(True)

plt.show()