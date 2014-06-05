## This code is written by Davide Albanese, <albanese@fbk.eu>
## (C) 2011 mlpy Developers.

## See: Practical Guide to Wavelet Analysis - C. Torrence and G. P. Compo.

## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.

## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.

## You should have received a copy of the GNU General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.

from numpy import *


PI2 = 2 * pi


def normalization(s, dt):
    return sqrt((PI2 * s) / dt)


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
    wavelet = zeros((s.shape[0], w.shape[0]))
    pos = w > 0

    for i in range(s.shape[0]):
        n = normalization(s[i], dt)
        wavelet[i][pos] = n * p * exp(-(s[i] * w[pos] - w0)**2 / 2.0)
        
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

    # See (5) at page 64.
    
    N2 = N / 2.0
    w = empty(N)

    for i in range(w.shape[0]):
        if i <= N2:
            w[i] = (2 * pi * i) / (N * dt)
        else:
            w[i] = (2 * pi * (i - N)) / (N * dt)

    return w


def autoscales(N, dt, dj, p):
     """Compute scales as fractional power of two.

     :Parameters:
        N : integer
           number of data samples
        dt : float
           time step
        dj : float
           scale resolution (smaller values of dj give finer resolution)
        p : float
           omega0 ('morlet')
     
     :Returns:
        scales : 1d numpy array
           scales
     """
     
     s0 = (dt * (p + sqrt(2 + p**2))) / (2 * pi)
     
     #  See (9) and (10) at page 67.

     J = floor(dj**-1 * log2((N * dt) / s0))
     s = empty(J + 1)
    
     for i in range(s.shape[0]):
         s[i] = s0 * 2**(i * dj)
    
     return s


def cwt(data, dt, scales, p=2):
    """Continuous Wavelet Tranform.

    :Parameters:
       data : 1d array_like object
          data
       dt : float
          time step
       scales : 1d array_like object
          scales
       p : float
          wavelet function parameter ('omega0' for morlet)
            
    :Returns:
       X : 2d numpy array
          transformed data
    """

    x_arr = asarray(data) - mean(data)
    scales_arr = asarray(scales)

    if x_arr.ndim is not 1:
        raise ValueError('data must be an 1d numpy array of list')

    if scales_arr.ndim is not 1:
        raise ValueError('scales must be an 1d numpy array of list')

    w = angularfreq(N=x_arr.shape[0], dt=dt)
        
    wft = morletft(s=scales_arr, w=w, w0=p, dt=dt)
    
    X_ARR = empty((wft.shape[0], wft.shape[1]), dtype=complex128)
        
    x_arr_ft = fft.fft(x_arr)

    for i in range(X_ARR.shape[0]):
        X_ARR[i] = fft.ifft(x_arr_ft * wft[i])
    
    return X_ARR


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
       p : float
          wavelet function parameter

    :Returns:
       x : 1d numpy array
          data
    """  
    
    X_arr = asarray(X)
    scales_arr = asarray(scales)

    if X_arr.shape[0] != scales_arr.shape[0]:
        raise ValueError('X, scales: shape mismatch')

    # See (11), (13) at page 68
    X_ARR = empty_like(X_arr)
    for i in range(scales_arr.shape[0]):
        X_ARR[i] = X_arr[i] / sqrt(scales_arr[i])
    
    x = sum(real(X_ARR), axis=0)
   
    return x
