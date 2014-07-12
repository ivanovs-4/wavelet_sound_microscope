import numpy as np
from matplotlib.colors import LinearSegmentedColormap


cmap = LinearSegmentedColormap.from_list(
    'lightfire',
    sorted([
        (1, (1, 1, 1)),
        (0.6, (1, .8, .3)),
        (0.4, (.8, .7, .1)),
        (0.2, (.0, .4, .7)),
        (0.05, (.0, .0, .6)),
        (0, (0, 0, 0)),
    ])
)


def apply_colormap(image):
    return 255 * cmap(image)[:, :, :3]


def nolmalize_horizontal_smooth(arr, window_len):
    maxes = np.abs(arr).max(axis=0)

    smoothed = smooth(maxes, window_len)
    smoothed[smoothed == 0] = 1

    norma = smoothed * (maxes / smoothed).max()

    arr /= norma


def test_smooth():
    assert smooth(np.linspace(-4, 4, 100)).shape[0] == 100
    assert smooth(np.linspace(-4, 4, 101)).shape[0] == 101
    assert smooth(np.linspace(-4, 4, 100), 13).shape[0] == 100
    assert smooth(np.linspace(-4, 4, 101), 13).shape[0] == 101
    assert smooth(np.linspace(-4, 4, 1000), 131).shape[0] == 1000
    assert smooth(np.linspace(-4, 4, 1001), 131).shape[0] == 1001


def smooth(x, window_len=11, window='hanning'):
    """
    Smooth the data using a window with requested size

    This method is based on the convolution of a scaled window with the signal.
    The signal is prepared by introducing reflected copies of the signal
    (with the window size) in both ends so that transient parts are minimized
    in the begining and end part of the output signal.
    """

    if window_len % 2 != 1:
        raise ValueError('window_len must be odd')

    if x.ndim != 1:
        raise ValueError('smooth only accepts 1 dimension arrays')

    if x.size < window_len:
        raise ValueError('Input vector needs to be bigger than window size')

    if window_len < 3:
        return x

    allowed = ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']

    if window not in allowed:
        raise ValueError('Window is on of %s' % allowed)

    s = np.r_[x[window_len - 1: 0: -1], x, x[-1: -window_len: -1]]

    if window == 'flat':  # moving average
        w = np.ones(window_len, 'd')

    else:
        w = eval('np.' + window + '(window_len)')

    y = np.convolve(w / w.sum(), s, mode='valid')

    return y[(window_len / 2): -(window_len / 2)]
