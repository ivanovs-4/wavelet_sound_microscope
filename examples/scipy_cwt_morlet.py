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

     p = 10.3
     s0 = (dt * (p + np.sqrt(2 + p**2))) / (2 * np.pi)

     # if wf == 'dog':
     #     s0 = (dt * sqrt(p + 0.5)) / pi
     # elif wf == 'paul':
     #     s0 = (dt * ((2 * p) + 1)) / (2 * pi)
     # elif wf == 'morlet':
     #     s0 = (dt * (2 + sqrt(2 + p**2))) / (2 * pi)
     # else:
     #     raise ValueError('wavelet function not available')
     
     #  See (9) and (10) at page 67.

     J = np.floor(dj**-1 * np.log2((N * dt) / s0))
     s = np.empty(J + 1)
    
     return [s0 * 2**(i * dj) for i in range(s.shape[0])]


x = np.random.sample(512)
# x += np.sin(np.array(range(len(x))) / 20.) / 5.
x = np.sin(np.array(range(len(x))) / 20.) / 5.
# x += np.sin(np.array(range(len(x))) / 5.) / 5.
# x += np.sin(np.array(range(len(x))) / 230.) / 5.

widths = autoscales(N=x.shape[0], dt=1, dj=0.1)
# widths = np.array(range(100)) + 10

cwtmatr = signal.cwt(x, signal.morlet, widths)
print cwtmatr

fig = plt.figure(1)

ax1 = plt.subplot(5,1,1)
p1 = ax1.plot(x)
ax1.autoscale_view(tight=True)

ax2 = plt.subplot(5,1,2)
p2 = ax2.plot(widths)
ax2.autoscale_view(tight=True)

ax3 = plt.subplot(5,1,3)
p3 = ax3.imshow(np.real(cwtmatr))
p3.set_cmap('copper')

ax4 = plt.subplot(5,1,4)
p4 = ax4.imshow(np.imag(cwtmatr))
p4.set_cmap('copper')

ax5 = plt.subplot(5,1,5)
p5 = ax5.imshow(np.abs(cwtmatr))
p5.set_cmap('copper')

fig.set_tight_layout(True)

plt.show()
