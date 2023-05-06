#!/usr/bin/env python3

import serial
import urwid
import threading
from queue import Queue
import time


class PortReader:
    def __init__(self, device_name):
        self.port = serial.Serial(device_name)
        self.queue = Queue()
        # Mapping between
        self.cache_state = {}
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

    def diff_with_last(self, parts):
        """Check if the state is unchanged, return array showing the locations of differences."""
        if parts[0] in self.cache_state:
            cache_value = self.cache_state[parts[0]]
            if cache_value == parts:
                # No difference
                return None
            if len(cache_value) != len(parts):
                # We don't expect the length to change for the same code, but if it doesn, it's all different
                return [True for _ in parts]
            else:
                # Check the individual fields for a change
                return [cache != current for cache, current in zip(cache_value, parts)]
        else:
            # All different
            return [True for _ in parts]

    def worker(self):
        while True:
            data = self.port.readline()
            try:
                line = data.decode()
            except UnicodeDecodeError:
                continue
            parts = line.strip().split(" ")
            if self.verify(parts):
                diff_spec = self.diff_with_last(parts)
                if diff_spec is None:
                    continue
                self.queue.put((parts, diff_spec))
                self.cache_state[parts[0]] = parts


# Dict with the visible mappings
VISIBLE_DATA = {
}


def render():
    """Return a text render of the visible data dict"""
    keys = list(VISIBLE_DATA.keys())
    keys.sort()
    text_elements = []
    for key in keys:
        data, diff_spec, time_written = VISIBLE_DATA[key]
        now = time.time()
        text_elements.append(f"{key:>4}")
        for value, changed in zip(data[2:], diff_spec[2:]):
            if now > (time_written + 2):
                changed = False
            text_elements.append(" ")
            if changed:
                text_elements.append(("red", f"{value:>2}"))
            else:
                text_elements.append(("default", f"{value:>2}"))

        text_elements.append("\n")
    return text_elements


def show_or_exit(key):
    if key in ('q', 'Q'):
        raise urwid.ExitMainLoop()


def update_text_from_queue(loop, user_data):
    text_queue, text_widget = user_data
    has_update = False
    while not text_queue.empty():
        has_update = True
        data, diff_spec = text_queue.get()
        VISIBLE_DATA[data[0]] = (data, diff_spec, time.time())
    if has_update:
        text_widget.set_text(render())
    loop.set_alarm_in(0.1, update_text_from_queue, user_data=(text_queue, text_widget))


def main():

    palette = {
        # name, foreground, background?
        ('default', 'default', ''),
        ('red', 'black', 'light red'),
    }

    txt = urwid.Text("")

    reader = PortReader('/dev/ttyACM0')

    fill = urwid.Filler(txt, 'top')

    loop = urwid.MainLoop(fill, palette=palette, unhandled_input=show_or_exit)

    update_text_from_queue(loop, (reader.queue, txt))

    loop.set_alarm_in(0.1, update_text_from_queue, user_data=(reader.queue, txt))
    loop.run()


if __name__ == "__main__":
    main()
