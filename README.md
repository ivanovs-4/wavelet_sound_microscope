wavelet_sound_microscope
========================

Wavelet spectroanalizator.
It performs calculations on nvidia CUDA GPU.

On Geforce GT 630 it is about 3 x realtime.


#### TODO muse_explorer
* Make chunks overlapping in BaseWaveletBox.apply_cwt
* Move fragment calculation to thread
* Universal play sound
* Fix PyCUDA ERROR: The context stack was not empty upon module cleanup.
* Long cache composition results
* Use smooth horizontal normalization
* Debian package
