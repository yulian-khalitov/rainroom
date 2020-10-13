import PySimpleGUI as sg


def get_window(lidars, grid):
    sg.theme('LightGrey1')
    layout = [
        [sg.Graph(canvas_size=(600, 600), graph_bottom_left=(0, -3000), graph_top_right=(6000, 3000),
                  background_color='white', key='-GRAPH-', enable_events=True)],
        [sg.Text('delay', key='-DELAY-', size=(10, 1))],
        [sg.Text('UNDEFINED', key='-SHOWERS STATE-', text_color='orange', size=(10, 1))],
        [sg.Text('x'), sg.Spin([i for i in range(-10000, 10000)], initial_value=grid.x0 // 10, key='-X-', enable_events=True),
         sg.Text('y'), sg.Spin([i for i in range(-10000, 10000)], initial_value=grid.y0 // 10, key='-Y-', enable_events=True),
         sg.Text('sensitivity'), sg.Spin([i for i in range(0, 10)], initial_value=0, key='-SENS-', enable_events=True)],
        [sg.Text('Points'), sg.Radio('all', 'RADIO3', key='-ALL-', enable_events=True),
         sg.Radio('inside grid', 'RADIO3', key='-INSIDE GRID-', enable_events=True, default=True)],
    ]
    for i, lidar in enumerate(lidars):

        layout.append(
            [sg.Checkbox(lidar.port, key='-LIDAR CHECK-' + str(i), enable_events=True, default=lidar.is_active),

             sg.ProgressBar(3000, orientation='h', size=(20, 20), key='-LIDAR BUFFER-' + str(i)),
             sg.Text('x'), sg.Spin([i for i in range(-10000, 10000)], initial_value=lidar.x_shift // 10, key='-LIDAR X-' + str(i), enable_events=True),
             sg.Text('y'), sg.Spin([i for i in range(-10000, 10000)], initial_value=lidar.y_shift // 10, key='-LIDAR Y-' + str(i), enable_events=True),
             sg.Text('0', key='-LIDAR RUNTIME-' + str(i), size=(10, 1)),],
        )
    layout += [[sg.Button('activate', key='-ACTIVATE-'), sg.Button('on all', key='-ON ALL-'),
                sg.Button('off all', key='-OFF ALL-')],
               [sg.Checkbox('interactive', key='-INTERACTIVE-', enable_events=True),
                sg.Checkbox('special', key='-SPECIAL-', enable_events=True)]]
    return sg.Window('Rainroom', layout, finalize=True)


def update_window(window, runtime, modbus_runtime, lidars):
    window['-DELAY-'].update('{:.3f}'.format(runtime))  # add modbus_runtime optionally
    for i, lidar in enumerate(lidars):
        window['-LIDAR BUFFER-' + str(i)].UpdateBar(lidar.buffer)
        window['-LIDAR RUNTIME-' + str(i)].update('{:.3f}'.format(lidar.runtime))


def set_window_disabled(window, disabled):
    if disabled:
        window['-DELAY-'].update('')
    for elem in window.element_list():
        try:
            elem.update(disabled=disabled)
        except:
            pass


def popup():
    sg.popup('Не удалось подключиться к контроллерам', non_blocking=True)



