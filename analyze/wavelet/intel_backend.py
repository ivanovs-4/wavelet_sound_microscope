import numpy as np
import py

from .base import BaseWaveletBox, PI2


class WaveletBox(BaseWaveletBox):

    def __init__(self, nsamples, samplerate, scale_resolution, omega0):
        super(WaveletBox, self). \
            __init__(nsamples, samplerate, scale_resolution, omega0)

        self.wft = morlet_ft_box(self.scales, self.angular_frequencies,
                                 omega0, samplerate)

    def cwt(self, data, decimate=None):

        x_arr = np.asarray(data, dtype=np.complex64) - np.mean(data)
        x_width = x_arr.shape[0]

        if x_arr.ndim is not 1:
            raise ValueError('data must be an 1d numpy array or list')

        assert x_arr.shape[0] == self.nsamples

        if decimate:
            result_width = len(list(range(self.nsamples))[::decimate])

        else:
            result_width = self.nsamples

        complex_image = np.empty((self.scales.shape[0], result_width),
                                 dtype=np.complex64)

        gpu_x_arr_ft = gpuarray.to_gpu(x_arr)
        self.plan.execute(gpu_x_arr_ft)

        gpu_med = gpuarray.empty_like(gpu_x_arr_ft)

        for i in range(complex_image.shape[0]):
            multiply_them(gpu_med, gpu_x_arr_ft, self.wft[i])

            self.plan.execute(gpu_med, inverse=True)

            if decimate:
                reshaped = gpu_med.reshape((result_width,
                                            x_width / result_width))

                gpu_decimated = extract_columns(reshaped, 0, 1).ravel()

                complex_image[i] = gpu_decimated.get()

            else:
                complex_image[i] = gpu_med.get()

        return complex_image


def normalization(scale, samplerate):
    return np.sqrt(PI2 * scale * samplerate)


def morlet_ft_box(scales, angular_frequencies, omega0, samplerate):
    """ Fourier tranformed morlet function """

    pi_sqr_1_4 = 0.75112554446494251  # pi**(-1.0/4.0)

    wavelet = [None] * scales.shape[0]

    gpu_angular_frequencies = gpuarray.to_gpu(angular_frequencies)

    for i in range(scales.shape[0]):
        norma = normalization(scales[i], samplerate)

        wavelet[i] = gpuarray.empty(
            (angular_frequencies.shape[0],),
            dtype=np.complex64
        )

        calculate_morlet(
            wavelet[i],
            norma * pi_sqr_1_4,
            scales[i],
            gpu_angular_frequencies,
            omega0
        )

    return wavelet


def extract_columns(mat, start, stop):
    stop = stop or start + 1
    dtype = mat.dtype
    itemsize = np.dtype(dtype).itemsize
    N, M = mat.shape
    m = stop - start

    assert mat.flags.c_contiguous
    assert 0 <= start < stop <= M

    new_mat = gpuarray.empty((N, m), dtype)

    copy = cuda.Memcpy2D()
    copy.set_src_device(mat.gpudata)
    copy.src_x_in_bytes = start * itemsize  # First column offset in bytes
    copy.set_dst_device(new_mat.gpudata)

    copy.src_pitch = int(M) * itemsize  # Source array row width in bytes
    copy.dst_pitch = copy.width_in_bytes = m * itemsize  # Width of sliced row
    copy.height = N
    copy(aligned=True)

    return new_mat
