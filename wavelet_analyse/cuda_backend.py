# -*- coding: utf-8 -*-
import numpy as np


BACKEND = 'cuda'

PI2 = 2 * np.pi


class WaveletBox(object):
    def __init__(self, N, dt=1, dj=1/9., p=np.pi):
        self.scales = self.autoscales(N, dt, dj, np.pi)
        self.angular_frequencies = angularfreq(N=N, dt=dt)

        self.wft = morletft(s=self.scales, w=self.angular_frequencies, w0=p, 
                            dt=dt)


    def cwt(self, data):
        x_arr = np.asarray(data) - np.mean(data)

        if x_arr.ndim is not 1:
            raise ValueError('data must be an 1d numpy array or list')

        assert x_arr.shape[0] == self.wft.shape[1]

        complex_image = np.empty((self.wft.shape[0], self.wft.shape[1]), 
                              dtype=np.complex128)

        x_arr_ft = np.fft.fft(x_arr)

        for i in range(complex_image.shape[0]):
            complex_image[i] = np.fft.ifft(x_arr_ft * self.wft[i])

        return complex_image


    def autoscales(self, N, dt, dj, p):
        """
        Compute scales as fractional power of two.

        :Parameters:
            N : integer : umber of data samples
            dt : float : time step
            dj : float : scale resolution 
            p : float : omega0 ('morlet')

        :Returns:
            scales : 1d numpy array
        """

        s0 = (dt * (p + np.sqrt(2 + p**2))) / PI2

        J = int(np.floor(dj**-1 * np.log2((N * dt) / s0)))

        return np.fromiter((s0 * 2**(i * dj) for i in range(J + 1)),
                           np.float, J + 1)


def normalization(s, dt):
    return np.sqrt(PI2 * s / dt)


def morletft(s, w, w0, dt):
    """Fourier tranformed morlet function.

    Input
      * *s*    - scales
      * *w*    - angular frequencies
      * *w0*   - omega0 (frequency)
      * *dt*   - time step
    Output
      * (normalized) fourier transformed morlet function
    """

    p = 0.75112554446494251 # pi**(-1.0/4.0)
    wavelet = np.zeros((s.shape[0], w.shape[0]))
    pos = w > 0

    for i in range(s.shape[0]):
        n = normalization(s[i], dt)
        wavelet[i][pos] = n * p * np.exp(-(s[i] * w[pos] - w0)**2 / 2.0)

    return wavelet


def angularfreq(N, dt):
    """Compute angular frequencies.

    :Parameters:
       N : integer
          number of data samples
       dt : float
          time step

    :Returns:
        angular frequencies : 1d numpy array
    """

    N2 = N / 2.0

    return np.fromiter(
        (
            PI2 * (i if i <= N2 else i - N) / (N * dt)
            for i in range(N)
        ),
        np.float, N
    )


'''
def icwt(X, dt, scales, p=2):
    """Inverse Continuous Wavelet Tranform.
    The reconstruction factor is not applied.

    :Parameters:
       X : 2d array_like object
          transformed data
       dt : float
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
