import math
import time
import multiprocessing
import logging
from rplidar import RPLidar  # use pip install rplidar-roboticia
from rplidar import RPLidarException
from datetime import datetime
from ctypes import c_bool, c_wchar_p


def lidar_process(scans, buffer, simple_grid, width, height, runtime, port, x0, y0, x1, y1, h,
                  x_shift, y_shift, is_active, is_all_points, scan_type='normal', max_buf_meas=3000, min_len=5):
    logger = logging.Logger('rplidar_' + port)

    date_time = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    f_handler = logging.FileHandler(port + '_' + date_time + '.log')
    f_handler.setLevel(logging.INFO)
    f_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(f_handler)

    lidar = RPLidar(port, logger=logger)
    scans_tmp = []
    simple_grid_tmp = [[0] * width for _ in range(height)]
    iterator = lidar.iter_measures(scan_type, max_buf_meas)
    scans_count = 0
    start = time.time()
    while True:
        try:
            new_scan, quality, angle, distance = next(iterator)
        except RPLidarException as e:
            lidar.logger.warning(e.args[0])
            iterator = lidar.iter_measures(scan_type, max_buf_meas)
            continue
        if new_scan:
            if scans_count > min_len:
                scans[:] = scans_tmp
                simple_grid[:] = simple_grid_tmp
                if not is_active.value:
                    scans[:] = []
                    simple_grid[:] = [[0] * width for _ in range(height)]
                    runtime.value = 0
                    buffer.value = 0
                    lidar.stop()
                    lidar.stop_motor()
                    lidar.disconnect()
                    return
                runtime.value = time.time() - start
                start = time.time()
            scans_count = 0
            simple_grid_tmp = [[0] * width for _ in range(height)]
            scans_tmp = []
        if distance > 0:
            x = distance * math.cos(math.radians(-angle)) + x_shift.value
            y = distance * math.sin(math.radians(-angle)) + y_shift.value
            is_in_grid = x0.value <= x <= x1.value and y0.value <= y <= y1.value
            if is_all_points.value or is_in_grid:
                scans_tmp.append((x, y))
            if is_in_grid:
                j = int((x - x0.value) / (h.value + 1))
                i = int((y - y0.value) / (h.value + 1))
                simple_grid_tmp[i][j] += 1
            scans_count += 1
        buffer.value = lidar._serial.inWaiting()


class Lidar:
    def __init__(self, manager, grid, settings_dict, port):
        lidar = RPLidar(port, timeout=0.5)
        lidar.stop()
        lidar.stop_motor()
        lidar_info = lidar.get_info()
        self._serial_number = manager.Value(c_wchar_p, lidar_info['serialnumber'])
        lidar.disconnect()
        settings = settings_dict.get(self.serial_number)
        self.grid = grid
        self.scans = manager.list()
        self._buffer = manager.Value('i', 0)
        self._runtime = manager.Value('d', 0.0)
        self.simple_grid = manager.list()
        self._x_shift = manager.Value('i', settings[1] if settings else 0)
        self._y_shift = manager.Value('i', settings[2] if settings else 0)
        self._is_active = manager.Value(c_bool, settings[0] if settings else True)
        self._is_all_points = manager.Value(c_bool, False)
        self.port = port
        self.scan_type = 'normal'
        self.max_buf_meas = 2000
        self.process = None
        if self.is_active:
            self.start()

    def start(self):
        self.process = multiprocessing.Process(target=lidar_process, kwargs={
            'scans': self.scans,
            'buffer': self._buffer,
            'simple_grid': self.simple_grid,
            'width': self.grid.width,
            'height': self.grid.height,
            'runtime': self._runtime,
            'x0': self.grid._x0,
            'y0': self.grid._y0,
            'x1': self.grid._x1,
            'y1': self.grid._y1,
            'h': self.grid._h,
            'x_shift': self._x_shift,
            'y_shift': self._y_shift,
            'is_active': self._is_active,
            'is_all_points': self._is_all_points,
            'port': self.port,
            'scan_type': self.scan_type,
            'max_buf_meas': self.max_buf_meas
        })
        self.is_active = True
        self.process.start()

    def stop(self):
        self.is_active = False
        while self.process.is_alive():
            time.sleep(.1)

    def restart(self):
        self.stop()
        self.start()

    @property
    def buffer(self):
        return self._buffer.value

    @buffer.setter
    def buffer(self, buffer):
        self._buffer.value = buffer

    @property
    def runtime(self):
        return self._runtime.value

    @runtime.setter
    def runtime(self, runtime):
        self._runtime.value = runtime

    @property
    def is_active(self):
        return self._is_active.value

    @is_active.setter
    def is_active(self, is_active):
        self._is_active.value = is_active

    @property
    def is_all_points(self):
        return self._is_all_points.value

    @is_all_points.setter
    def is_all_points(self, is_all_points):
        self._is_all_points.value = is_all_points

    @property
    def x_shift(self):
        return self._x_shift.value

    @x_shift.setter
    def x_shift(self, x_shift):
        self._x_shift.value = x_shift

    @property
    def y_shift(self):
        return self._y_shift.value

    @y_shift.setter
    def y_shift(self, y_shift):
        self._y_shift.value = y_shift

    @property
    def serial_number(self):
        return self._serial_number.value

    @serial_number.setter
    def serial_number(self, serial_number):
        self._serial_number.value = serial_number
