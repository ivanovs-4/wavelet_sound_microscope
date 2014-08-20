import collections


class cached_property(object):
    def __init__(self, func):
        self.func = func

    def __get__(self, instance, type=None):
        if instance is None:
            return self
        res = instance.__dict__[self.func.__name__] = self.func(instance)
        return res


class CountedIterable(collections.Iterator):
    def __init__(self, iterable, length):
        self.iterable = iterable
        self.length = length

    def __len__(self):
        return self.length

    def __next__(self):
        self.length -= 1

        return next(self.iterable)
