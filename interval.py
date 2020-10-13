from threading import Timer
from functools import partial


class Interval:
    def __init__(self, interval, function, args=[], kwargs={}):
        self.interval = interval
        self.function = partial(function, *args, **kwargs)
        self.running = False
        self._timer = None

    def __call__(self):
        self.running = False
        self.start()
        self.function()

    def start(self):
        if self.running:
            return
        self._timer = Timer(self.interval, self)
        self._timer.start()
        self.running = True

    def stop(self):
        if self._timer:
            self._timer.cancel()
        self.running = False
        self._timer = None
