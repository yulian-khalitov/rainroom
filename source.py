#!/usr/bin/python
import time
import multiprocessing
import serial.tools.list_ports
import socket
import json
import PySimpleGUI as sg
import gui
from grid import Grid
from lidar import Lidar
from interval import Interval
from modbus_tk import modbus_rtu_over_tcp


def special_mode(grid, master):
    if grid.last_static_mode:
        grid.off_all(master)
    else:
        grid.on_all(master)


def save_settings(lidars, grid):
    settings = {}
    for lidar in lidars:
        settings[lidar.serial_number] = lidar.is_active, lidar.x_shift, lidar.y_shift
    settings['x'] = grid.x0
    settings['y'] = grid.y0
    settings['sens'] = grid.sens
    with open('settings.cfg', 'w') as file:
        json.dump(settings, file)


def load_settings():
    try:
        with open('settings.cfg', 'r') as file:
            return json.load(file)
    except:
        return {'x': 0, 'y': 0, 'sens': 0}


def main():
    settings = load_settings()
    com_ports = [com[0] for com in serial.tools.list_ports.comports() if com[0] != 'COM1']
    grid = Grid(settings)
    manager = multiprocessing.Manager()
    lidars = [Lidar(manager, grid, settings, com) for i, com in enumerate(com_ports)]
    window = gui.get_window(lidars, grid)
    graph = window['-GRAPH-']
    colors = ['red', 'blue', 'orange', 'pink']
    master = modbus_rtu_over_tcp.RtuOverTcpMaster(host='192.168.0.191', port=9761, timeout_in_sec=0.5)
    modbus_runtime = 0
    while True:
        start = time.time()
        grid.reset_state()
        graph.Erase()
        grid.update_states(lidars)
        grid.print(graph)

        for color, lidar in zip(colors, lidars):
            for x, y in lidar.scans:
                graph.DrawCircle((x, y), 20, line_color=color, fill_color=color)

        event, values = window.read(timeout=0)

        if event == sg.WIN_CLOSED:
            for lidar in lidars:
                if lidar.is_active:
                    lidar.stop()
            return
        if event == '-X-':
            grid.x0 = values['-X-'] * 10
            grid.x1 = grid.x0 + grid.width * (grid.h + 1)
            save_settings(lidars, grid)
        if event == '-Y-':
            grid.y0 = values['-Y-'] * 10
            grid.y1 = grid.y0 + grid.height * (grid.h + 1)
            save_settings(lidars, grid)
        if event == '-SENS-':
            grid.sens = values['-SENS-']
            save_settings(lidars, grid)
        if event == '-ACTIVATE-':
            window['-SHOWERS STATE-'].update('ACTIVE', text_color='green')
            grid.activate()
        if event == '-ON ALL-':
            grid.deactivate()
            try:
                grid.on_all(master)
                window['-SHOWERS STATE-'].update('ON ALL', text_color='green')
            except socket.timeout:
                gui.popup()
                window['-SHOWERS STATE-'].update('UNDEFINED', text_color='orange')
        if event == '-OFF ALL-':
            grid.deactivate()
            try:
                grid.off_all(master)
                window['-SHOWERS STATE-'].update('OFF ALL', text_color='red')
            except socket.timeout:
                gui.popup()
                window['-SHOWERS STATE-'].update('UNDEFINED', text_color='orange')

        if event == '-INTERACTIVE-':
            grid.deactivate()
            grid.reset_state()
            grid.off_all(master)
            gui.set_window_disabled(window, True)
            window['-INTERACTIVE-'].update(disabled=False)
            window['-SHOWERS STATE-'].update('INTERACTIVE', text_color='green')
            for lidar in lidars:
                if lidar.is_active:
                    lidar.stop()
            while True:
                graph.Erase()
                grid.print_interactive(graph)
                event, values = window.read(timeout=0)
                if event == sg.WIN_CLOSED:
                    grid.off_all(master)
                    return
                if event == '-INTERACTIVE-':
                    break
                # here was is_socket_open() check
                if event == '-GRAPH-' and master is not None:
                    x = values['-GRAPH-'][0]
                    y = values['-GRAPH-'][1]
                    try:
                        grid.switch(master, x, y)
                    except socket.timeout:
                        gui.popup()
            try:
                grid.off_all(master)
                window['-SHOWERS STATE-'].update('OFF ALL', text_color='red')
            except socket.timeout:
                window['-SHOWERS STATE-'].update('UNDEFINED', text_color='orange')
            gui.set_window_disabled(window, False)
            # grid.set_prev_state()
            for i, lidar in enumerate(lidars):
                if values['-LIDAR CHECK-' + str(i)]:
                    lidar.start()
        if event == '-SPECIAL-':
            grid.deactivate()
            grid.reset_state()
            grid.on_all(master)
            gui.set_window_disabled(window, True)
            for lidar in lidars:
                if lidar.is_active:
                    lidar.stop()
            window['-SPECIAL-'].update(disabled=False)
            window['-SHOWERS STATE-'].update('')
            interval = Interval(5, special_mode, args=[grid, master])
            interval.start()
            while True:
                graph.Erase()
                grid.print(graph)
                event, values = window.read(timeout=0)
                if event in (sg.WIN_CLOSED, '-SPECIAL-'):
                    break
            interval.stop()
            try:
                grid.off_all(master)
                window['-SHOWERS STATE-'].update('OFF ALL', text_color='red')
            except socket.timeout:
                window['-SHOWERS STATE-'].update('UNDEFINED', text_color='orange')
            if event == sg.WIN_CLOSED:
                return
            gui.set_window_disabled(window, False)
            grid.set_prev_state()
            for i, lidar in enumerate(lidars):
                if values['-LIDAR CHECK-' + str(i)]:
                    lidar.start()
        for i, lidar in enumerate(lidars):
            lidar.is_all_points = values['-ALL-']
            if event == '-LIDAR CHECK-' + str(i):
                if values['-LIDAR CHECK-' + str(i)]:
                    lidar.start()
                else:
                    lidar.stop()
                save_settings(lidars, grid)
            if event == '-LIDAR X-' + str(i):
                lidar.x_shift = values['-LIDAR X-' + str(i)] * 10
                save_settings(lidars, grid)
            if event == '-LIDAR Y-' + str(i):
                lidar.y_shift = values['-LIDAR Y-' + str(i)] * 10
                save_settings(lidars, grid)
        try:
            modbus_runtime = grid.update_showers(master)
        except socket.timeout:
            grid.deactivate()
            window['-SHOWERS STATE-'].update('UNDEFINED', text_color='orange')
            gui.popup()

        runtime = time.time() - start
        gui.update_window(window, runtime, modbus_runtime, lidars)


if __name__ == '__main__':
    main()
