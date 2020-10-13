import modbus_tk.defines as cst
import PySimpleGUI as sg
import time
import multiprocessing
from enum import Enum, auto


class State(Enum):
    CLEAR = auto()
    GREEN = auto()
    YELLOW = auto()
3

class Mode(Enum):
    ON = auto()
    OFF = auto()


class Shower:
    def __init__(self):
        self.rs_num = None
        self.led_num = None
        self.is_on = False
        self.is_off = True
        self.state = State.CLEAR
        self.point_count = 0

    def on(self, master):
        master.execute(self.rs_num, cst.WRITE_SINGLE_REGISTER, self.led_num + 1, output_value=255)
        self.is_on = True
        self.is_off = False

    def off(self, master):
        master.execute(self.rs_num, cst.WRITE_SINGLE_REGISTER, self.led_num + 1, output_value=0)
        self.is_on = False
        self.is_off = True


class Grid:
    def __init__(self, settings):
        manager = multiprocessing.Manager()
        self._x0 = manager.Value('i', 0 if not settings else settings['x'])
        self._y0 = manager.Value('i', 0 if not settings else settings['y'])
        self._h = manager.Value('i', 600)
        self.height = 4
        self.width = 5
        self._x1 = manager.Value('i', self.x0 + self.width * (self.h + 1))
        self._y1 = manager.Value('i', self.y0 + self.height * (self.h + 1))
        self.is_active_prev = False
        self.is_active = False
        self.last_static_mode = False
        self.sens = 0
        rs_i = 1
        led_i = 0
        self.showers = [[Shower() for _ in range(self.width)] for _ in range(self.height)]
        for i in range(self.height - 1, -1, -1):
            for j in range(1, self.width):
                if led_i > 5:
                    rs_i += 1
                    led_i = 0
                self.showers[i][j].rs_num = rs_i
                self.showers[i][j].led_num = led_i
                led_i += 1

    @property
    def x0(self):
        return self._x0.value

    @x0.setter
    def x0(self, x0):
        self._x0.value = x0

    @property
    def y0(self):
        return self._y0.value

    @y0.setter
    def y0(self, y0):
        self._y0.value = y0

    @property
    def x1(self):
        return self._x1.value

    @x1.setter
    def x1(self, x1):
        self._x1.value = x1

    @property
    def y1(self):
        return self._y1.value

    @y1.setter
    def y1(self, y1):
        self._y1.value = y1

    @property
    def h(self):
        return self._h.value

    @h.setter
    def h(self, h):
        self._h.value = h

    def _print_grid(self, graph):
        for i in range(self.height + 1):
            graph.DrawLine((self.x0, self.y0 + i * self.h), (self.x0 + self.h * self.width, self.y0 + i * self.h))
        for i in range(self.width + 1):
            graph.DrawLine((self.x0 + i * self.h, self.y0), (self.x0 + i * self.h, self.y0 + self.h * self.height))

    def print(self, graph):
        self._print_grid(graph)
        for i in range(self.height):
            for j in range(self.width):
                shower = self.showers[i][j]
                if shower.state is State.GREEN:
                    graph.DrawRectangle((self.x0 + j * self.h, self.y0 + i * self.h),
                                        (self.x0 + (j + 1) * self.h, self.y0 + (i + 1) * self.h),
                                        fill_color='green')
                elif shower.state is State.YELLOW:
                    graph.DrawRectangle((self.x0 + j * self.h, self.y0 + i * self.h),
                                        (self.x0 + (j + 1) * self.h, self.y0 + (i + 1) * self.h),
                                        fill_color='yellow')
                if shower.rs_num is not None:
                    text = str(shower.rs_num) + ' ' + str(shower.led_num)
                    graph.DrawText(text, (self.x0 + j * self.h, self.y0 + i * self.h),
                                   text_location=sg.TEXT_LOCATION_BOTTOM_LEFT)

    def print_interactive(self, graph):
        self._print_grid(graph)
        for i in range(self.height):
            for j in range(self.width):
                shower = self.showers[i][j]
                if shower.rs_num is None:
                    continue
                if shower.is_off:
                    graph.DrawRectangle((self.x0 + j * self.h, self.y0 + i * self.h),
                                        (self.x0 + (j + 1) * self.h, self.y0 + (i + 1) * self.h),
                                        fill_color='red')
                elif shower.is_on:
                    graph.DrawRectangle((self.x0 + j * self.h, self.y0 + i * self.h),
                                        (self.x0 + (j + 1) * self.h, self.y0 + (i + 1) * self.h),
                                        fill_color='green')
                text = str(shower.rs_num) + ' ' + str(shower.led_num)
                graph.DrawText(text, (self.x0 + j * self.h, self.y0 + i * self.h),
                               text_location=sg.TEXT_LOCATION_BOTTOM_LEFT)

    def reset_state(self):
        for line in self.showers:
            for shower in line:
                shower.state = State.CLEAR
                shower.point_count = 0

    def update_green_state(self):
        for i, line in enumerate(self.showers):
            for j, shower in enumerate(line):
                if j == 0 and i == 3:
                    continue
                if i == 3 and j == 2:
                    if shower.point_count > 5:
                        shower.state = State.GREEN
                    continue
                if shower.point_count > self.sens:
                    shower.state = State.GREEN

    def update_yellow_state(self):
        def yellow(_i, _j):
            if 0 <= _i < self.height and 0 <= _j < self.width \
                    and (self.showers[_i][_j].state is State.CLEAR or self.showers[_i][_j].state is State.YELLOW):
                self.showers[_i][_j].state = State.YELLOW

        for i, line in enumerate(self.showers):
            for j, shower in enumerate(line):
                if shower.state is State.GREEN:
                    yellow(i - 1, j - 1)
                    yellow(i - 1, j)
                    yellow(i - 1, j + 1)
                    yellow(i, j + 1)
                    yellow(i + 1, j + 1)
                    yellow(i + 1, j)
                    yellow(i + 1, j - 1)
                    yellow(i, j - 1)

    def update_showers(self, client):
        start = time.time()
        if self.is_active:
            for line in self.showers:
                for shower in line:
                    if shower.rs_num is not None:
                        if shower.state in (State.GREEN, State.YELLOW) and shower.is_on:
                            shower.off(client)
                        elif shower.state is State.CLEAR and shower.is_off:
                            shower.on(client)
        return time.time() - start

    def on_all(self, client):
        for line in self.showers:
            for shower in line:
                if shower.rs_num is not None:
                    shower.state = State.GREEN
                    shower.on(client)
        self.last_static_mode = True

    def off_all(self, client):
        for line in self.showers:
            for shower in line:
                if shower.rs_num is not None:
                    shower.state = State.CLEAR
                    shower.off(client)
        self.last_static_mode = False

    def activate(self):
        self.is_active_prev = self.is_active
        self.is_active = True

    def deactivate(self):
        self.is_active_prev = self.is_active
        self.is_active = False

    def set_prev_state(self):
        self.is_active = self.is_active_prev

    def update_counts(self, x, y):
        if self.x0 <= x <= self.x1 and self.y0 <= y <= self.y1:
            j = int((x - self.x0) / (self.h + 1))
            i = int((y - self.y0) / (self.h + 1))
            self.showers[i][j].point_count += 1

    def switch(self, client, x, y):
        if self.x0 < x < self.x1 and self.y0 < y < self.y1:
            j = int((x - self.x0) / (self.h + 1))
            i = int((y - self.y0) / (self.h + 1))
            shower = self.showers[i][j]
            if shower.rs_num is not None:
                if shower.is_on:
                    shower.off(client)
                else:
                    shower.on(client)

    def start_test(self, master, window):
        self.off_all(master)
        graph = window['graph']
        while True:
            for line in self.showers:
                for shower in line:
                    if shower.rs_num is not None:
                        shower.state = State.GREEN
                        shower.on(master)
            graph.Erase()
            self.print(graph, False)
            event, values = window.read(timeout=0)
            if event == sg.WIN_CLOSED:
                return
            time.sleep(5)
            for line in self.showers:
                for shower in line:
                    if shower.rs_num is not None:
                        shower.state = State.CLEAR
                        shower.off(master)
            graph.Erase()
            self.print(graph, False)
            event, values = window.read(timeout=0)
            if event == sg.WIN_CLOSED:
                return
            time.sleep(5)

    def update_states(self, lidars):
        for lidar in lidars:
            for line, simple_line in zip(self.showers, lidar.simple_grid):
                for shower, count in zip(line, simple_line):
                    shower.point_count += count
        self.update_green_state()
        self.update_yellow_state()