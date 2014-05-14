import numpy as np
import matplotlib.pyplot as plt
from scipy import signal


def autoscales(N, dt, dj):
     """Compute scales as fractional power of two.

     :Parameters:
        N : integer
           number of data samples
        dt : float
           time step
        dj : float
           scale resolution (smaller values of dj give finer resolution)
        wf : string
           wavelet function ('morlet', 'paul', 'dog')
        p : float
           omega0 ('morlet') or order ('paul', 'dog')
     
     :Returns:
        scales : 1d numpy array
           scales
     """
     
     order = 2
     s0 = (dt * np.sqrt(order + 0.5)) / np.pi

     # if wf == 'dog':
     #     s0 = (dt * sqrt(p + 0.5)) / pi
     # elif wf == 'paul':
     #     s0 = (dt * ((2 * p) + 1)) / (2 * pi)
     # elif wf == 'morlet':
     #     s0 = (dt * (p + sqrt(2 + p**2))) / (2 * pi)
     # else:
     #     raise ValueError('wavelet function not available')
     
     #  See (9) and (10) at page 67.

     J = np.floor(dj**-1 * np.log2((N * dt) / s0))
     s = np.empty(J + 1)
    
     return [s0 * 2**(i * dj) for i in range(s.shape[0])]


x = np.random.sample(840)
x += np.sin(np.array(range(len(x))) / 20.) / 5.

widths = autoscales(N=x.shape[0], dt=1, dj=0.1)

wavelet = signal.ricker
cwtmatr = signal.cwt(x, wavelet, widths)

fig = plt.figure(1)

ax1 = plt.subplot(3,1,1)
p1 = ax1.plot(x)
ax1.autoscale_view(tight=True)

ax2 = plt.subplot(3,1,2)
p2 = ax2.imshow(cwtmatr, interpolation='nearest')

ax3 = plt.subplot(3,1,3)
p3 = ax3.plot(widths)
ax3.autoscale_view(tight=True)

fig.set_tight_layout(True)

plt.show()
