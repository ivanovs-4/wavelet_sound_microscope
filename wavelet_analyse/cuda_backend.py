# -*- coding: utf-8 -*-
import numpy as np
import pycuda.autoinit
import pycuda.driver as cuda
import pycuda.gpuarray as gpuarray
from pycuda.elementwise import ElementwiseKernel
from pyfft.cuda import Plan


BACKEND = 'cuda'

PI2 = 2 * np.pi


gpu_morlet = ElementwiseKernel(
    'pycuda::complex<float> *dest, '
    'float normal_pi_sqr_1_4, '
    'float scale, '
    'float *angular_frequencies, '
    'float omega0',
    'dest[i] = normal_pi_sqr_1_4 * powf(exp(-(scale * angular_frequencies[i] - omega0)), 2.0) / 2.0',
    'gpu_morlet',
    preamble='''#include <pycuda-complex.hpp>'''
)


multiply_them = ElementwiseKernel(
    "pycuda::complex<float> *dest, pycuda::complex<float> *left, pycuda::complex<float> *right",
    "dest[i] = left[i] * right[i]",
    "multiply_them",
    preamble='''#include <pycuda-complex.hpp>'''
)


class WaveletBox(object):
    def __init__(self, nsamples, time_step, scale_resolution, omega0):
        self.scales = self.autoscales(nsamples, time_step, scale_resolution, omega0)
        self.angular_frequencies = angularfreq(nsamples, time_step)

        self.wft = morletft(self.scales, self.angular_frequencies, omega0,
                            time_step)

        self.wft_gpu_i = [gpuarray.to_gpu(np.array(wft_i, dtype=np.complex64))
                          for wft_i in self.wft]

        stream = cuda.Stream()

        self.plan = Plan((nsamples,), stream=stream)


    def cwt(self, data, decimate=None):
        x_arr = np.asarray(data, dtype=np.complex64) - np.mean(data)
        x_width = x_arr.shape[0]

        if x_arr.ndim is not 1:
            raise ValueError('data must be an 1d numpy array or list')

        assert x_arr.shape[0] == self.wft.shape[1]

        if decimate:
            result_width = len(self.wft[0][::decimate])

        else:
            result_width = self.wft.shape[1]

        complex_image = np.empty((self.wft.shape[0], result_width),
                                 dtype=np.complex64)

        gpu_x_arr_ft = gpuarray.to_gpu(x_arr)
        self.plan.execute(gpu_x_arr_ft)

        gpu_med = gpuarray.empty_like(gpu_x_arr_ft)

        for i in range(complex_image.shape[0]):
            multiply_them(gpu_med, gpu_x_arr_ft, self.wft_gpu_i[i])

            self.plan.execute(gpu_med, inverse=True)

            if decimate:
                reshaped = gpu_med.reshape((result_width,
                                            x_width / result_width))

                gpu_decimated = extract_columns(reshaped, 0, 1).ravel()

                complex_image[i] = gpu_decimated.get()

            else:
                complex_image[i] = gpu_med.get()

        return complex_image


    def autoscales(self, nsamples, time_step, scale_resolution, omega0):
        """
        Compute scales as fractional power of two.

        :Parameters:
            nsamples : integer : umber of data samples
            time_step : float : time step
            scale_resolution : float : scale resolution
            omega0 : float : omega0 ('morlet')

        :Returns:
            scales : 1d numpy array
        """

        s0 = (time_step * (omega0 + np.sqrt(2 + omega0**2))) / PI2

        J = int(np.floor(scale_resolution**-1 * np.log2((nsamples * time_step) / s0)))

        return np.fromiter((s0 * 2**(i * scale_resolution) for i in range(J + 1)),
                           np.float, J + 1)


def normalization(s, time_step):
    return np.sqrt(PI2 * s / time_step)


def morletft(s, w, omega0, time_step):
    """Fourier tranformed morlet function.

    Input
      * *s*    - scales
      * *w*    - angular frequencies
      * *omega0*   - omega0 (frequency)
      * *time_step*   - time step
    Output
      * (normalized) fourier transformed morlet function
    """

    p = 0.75112554446494251 # pi**(-1.0/4.0)
    wavelet = np.zeros((s.shape[0], w.shape[0]))
    pos = w > 0

    for i in range(s.shape[0]):
        n = normalization(s[i], time_step)
        wavelet[i][pos] = n * p * np.exp(-(s[i] * w[pos] - omega0)**2 / 2.0)

    return wavelet


def angularfreq(nsamples, time_step):
    """Compute angular frequencies.

    :Parameters:
       nsamples : integer
          number of data samples
       time_step : float
          time step

    :Returns:
        angular frequencies : 1d numpy array
    """

    N2 = nsamples / 2.0

    return np.fromiter(
        (
            PI2 * (i if i <= N2 else i - nsamples) / (nsamples * time_step)
            for i in range(nsamples)
        ),
        np.float, nsamples
    )


'''
def icwt(X, time_step, scales, omega0=2):
    """Inverse Continuous Wavelet Tranform.
    The reconstruction factor is not applied.

    :Parameters:
       X : 2d array_like object
          transformed data
       time_step : float
          time step
       scales : 1d array_like object
          scales

    :Returns:
       x : 1d numpy array
          data
    """

    X_arr = asarray(X)
    scales_arr = asarray(scales)

    if X_arr.shape[0] != scales_arr.shape[0]:
        raise ValueError('X, scales: shape mismatch')

    X_ARR = empty_like(X_arr)
    for i in range(scales_arr.shape[0]):
        X_ARR[i] = X_arr[i] / sqrt(scales_arr[i])

    x = sum(real(X_ARR), axis=0)

    return x
'''


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
    copy.src_pitch = M * itemsize  # Source array row width in bytes
    copy.dst_pitch = copy.width_in_bytes = m * itemsize  # Width of sliced row
    copy.height = N
    copy(aligned=True)

    return new_mat
