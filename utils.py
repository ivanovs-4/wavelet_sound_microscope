import collections
import math


class cached_property(object):
    def __init__(self, func):
        self.func = func

    def __get__(self, instance, type=None):
        if instance is None:
            return self
        res = instance.__dict__[self.func.__name__] = self.func(instance)
        return res


class IterableWithLength(collections.Iterator):
    def __init__(self, iterable, length):
        self._iterable = iter(iterable)
        self.length = length

    def __len__(self):
        return self.length

    def __next__(self):
        self.length -= 1

        return next(self._iterable)


class ProgressProxy(collections.Iterator):
    def __init__(self, iterable, length=None):
        if length is None:
            length = _length_hint(iterable)
        if iterable is None:
            if length is None:
                raise TypeError('iterable or length is required')
            iterable = range_type(length)
        self._iterable = iter(iterable)
        self.length = length
        self.pos = 0
        self.entered = False

    def __enter__(self):
        self.entered = True
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.done()

    def __iter__(self):
        if not self.entered:
            raise RuntimeError('You need to use progress bars in a with block.')

        self.render_progress()

        return self

    def __next__(self):
        rv = next(self._iterable)
        self.make_step()
        self.render_progress()

        return rv

    def start(self):
        pass

    def make_step(self):
        self.pos += 1

    def render_progress(self):
        pass

    def done(self):
        pass


def _length_hint(obj):
    """Returns the length hint of an object."""
    try:
        return len(obj)
    except TypeError:
        try:
            get_hint = type(obj).__length_hint__
        except AttributeError:
            return None
        try:
            hint = get_hint(obj)
        except TypeError:
            return None
        if hint is NotImplemented or \
           not isinstance(hint, (int, long)) or \
           hint < 0:
            return None
        return hint


def round_significant(value, count=1):
    return round(value, count - 1 - math.floor(math.log10(value)))
