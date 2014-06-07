import sys

import numpy as np
from scipy.ndimage import interpolation
import matplotlib.pyplot as plt
from scipy.io import wavfile

import wavelet_continuous as wave


bitrate, wav = wavfile.read('sample.wav')

y = wav[:bitrate * 2, 0]

scales = wave.autoscales(N=y.shape[0], dt=1, dj=1/9.)

compex_image = wave.cwt(y, dt=1, scales=scales)

abs_image = np.abs(compex_image)

image = interpolation.zoom(abs_image, (1, 1. * 100 / bitrate))

fig = plt.figure(1)

ax = plt.subplot(1,1,1)
p = ax.imshow(image)
p.set_cmap('copper')

fig.set_tight_layout(True)

plt.show()
