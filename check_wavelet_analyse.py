import sys

import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile

# from wavelet_analyse import WaveletBox, BACKEND
from wavelet_analyse.cuda_backend import WaveletBox, BACKEND

print 'Backend:', BACKEND

fig = plt.figure(1)

bitrate, stereo_wav = wavfile.read('sample.wav')

wav = stereo_wav.transpose()[0]

# Make n_samples as power of two. More than one second
n_samples = 2**(1 + int(np.log2(bitrate - 1)))

print 'Bitrate:', bitrate
print 'N samples:', n_samples

wbox = WaveletBox(N=n_samples, dt=1, dj=1/24., p=30)

n_images = (wav.shape[0] - 1) / n_samples + 1
print 'N images:', n_images

padded_wav_size = n_images * n_samples

wav_pieces = np.pad(wav, (0, padded_wav_size - wav.shape[0]), 'constant') \
    .reshape((n_images, n_samples))


for j, y in enumerate(wav_pieces):
    compex_image = wbox.cwt(y, decimate=bitrate / 50)

    image = np.abs(compex_image)

    ax = plt.subplot(1, n_images, j + 1)
    ax.set_xticklabels( () )
    ax.set_yticklabels( () )
    p = ax.imshow(image)
    p.set_cmap('copper')

fig.set_tight_layout(True)

plt.show()
