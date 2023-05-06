#!/usr/bin/env python3

import serial
import urwid
import threading
from queue import Queue


class PortReader:
    def __init__(self, device_name):
        self.port = serial.Serial(device_name)
        self.queue = Queue()
        # Mapping between
        self.current_state = {}
        self.worker_thread = threading.Thread(target=self.worker)
        self.worker_thread.daemon = True
        self.worker_thread.start()

    @staticmethod
    def verify(parts):
        """Verify the received newline-terminated packet"""
        if len(parts) < 3:
            return False
        try:
            remain = int(parts[1])
            if remain != len(parts[2:]):
                return False
        except ValueError:
            return False
        return True

    def has_value(self, parts):
        """Check if the state is unchanged"""
        if parts[0] in self.current_state:
            if self.current_state[parts[0]] == parts:
                return True
        return False

    def worker(self):
        while True:
            data = self.port.readline()
            try:
                line = data.decode()
            except UnicodeDecodeError:
                continue
            parts = line.strip().split(" ")
            if self.verify(parts):
                if not self.has_value(parts):
                    self.queue.put(parts)
                    self.current_state[parts[0]] = parts


# Dict with the visible mappings
VISIBLE_DATA = {
}


def render():
    """Return a text render of the visible data dict"""
    keys = list(VISIBLE_DATA.keys())
    keys.sort()
    lines = []
    for key in keys:
        data = "".join([f" {_:>2}" for _ in VISIBLE_DATA[key][2:]])
        lines.append(f"{key:>4}-{data}")
    return "\n".join(lines)


def show_or_exit(key):
    if key in ('q', 'Q'):
        raise urwid.ExitMainLoop()


def update_text_from_queue(loop, user_data):
    text_queue, text_widget = user_data
    has_update = False
    while not text_queue.empty():
        has_update = True
        data = text_queue.get()
        VISIBLE_DATA[data[0]] = data
    if has_update:
        text_widget.set_text(render())
    loop.set_alarm_in(0.1, update_text_from_queue, user_data=(text_queue, text_widget))


def main():

    txt = urwid.Text("")

    reader = PortReader('/dev/ttyACM0')

    fill = urwid.Filler(txt, 'top')
    loop = urwid.MainLoop(fill, unhandled_input=show_or_exit)
    update_text_from_queue(loop, (reader.queue, txt))
    loop.set_alarm_in(0.1, update_text_from_queue, user_data=(reader.queue, txt))
    loop.run()


if __name__ == "__main__":
    main()
