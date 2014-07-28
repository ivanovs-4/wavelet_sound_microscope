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


class ProgressBar(object):
    def __init__(self, iterable, length=None, label=None):
        self.label = label or ''

        if length is None:
            length = _length_hint(iterable)
        if iterable is None:
            if length is None:
                raise TypeError('iterable or length is required')
            iterable = range_type(length)
        self.iter = iter(iterable)
        self.length = length
        self.pos = 0
        self.entered = False

    def __enter__(self):
        self.entered = True
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.render_finish()

    def __iter__(self):
        if not self.entered:
            raise RuntimeError('You need to use progress bars in a with block.')
        self.render_progress()
        return self

    def render_finish(self):
        pass

    def render_progress(self):
        pass

    def make_step(self):
        self.pos += 1
        if self.length_known and self.pos >= self.length:
            self.finished = True

        if (time.time() - self.last_eta) < 1.0:
            return

        self.last_eta = time.time()
        self.avg = self.avg[-6:] + [-(self.start - time.time()) / (self.pos)]

        self.eta_known = self.length_known

    def finish(self):
        self.eta_known = 0
        self.current_item = None
        self.finished = True

    def __next__(self):
        if self.is_hidden:
            return next(self.iter)
        try:
            rv = next(self.iter)
            self.current_item = rv
        except StopIteration:
            self.finish()
            self.render_progress()
            raise StopIteration()
        else:
            self.make_step()
            self.render_progress()
            return rv

