wavelet_sound_microscope
========================

Wavelet spectroanalizator.
It performs calculations on nvidia CUDA GPU.

On Geforce GT 630 it is about 3 x realtime.


#### TODO muse_explorer 
* Run composition.get_image() in thread.
  - Fix PyCUDA ERROR: The context stack was not empty upon module cleanup.
  - Implement loop breaking
* Create progressbar
* Long cache composition results
* Use smooth horizontal normalization
* Spectrogram area selection
