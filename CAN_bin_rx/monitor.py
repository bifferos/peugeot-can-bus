#!/usr/bin/env python3

import serial
import urwid
import threading
from queue import Queue
import time
import base64
import struct


class PortReader:
    def __init__(self, device_name):
        self.port = serial.Serial(device_name, baudrate=115200)
        self.reading_frame = []
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

    def diff_with_last(self, ident, parts):
        """Check if the state is unchanged, return array showing the locations of differences."""
        if ident in self.cache_state:
            cache_value = self.cache_state[ident]
            if cache_value == parts:
                # No difference
                return None
            if len(cache_value) != len(parts):
                return [True for _ in parts]
            else:
                # Check the individual fields for a change
                return [cache != current for cache, current in zip(cache_value, parts)]
        else:
            # All different
            return [True for _ in parts]

    def is_end_of_frame(self):
        self.reading_frame.append(self.port.read()[0])
        if self.reading_frame[-1] & (1 << 7):
            return True
        return False

    def decode_frame(self):
        """Ignoring the final byte (start of the next frame) extract the data"""
        rx_bytes = [_ for _ in self.reading_frame]
        self.reading_frame.clear()

        framing_byte = rx_bytes.pop()
        total_length = framing_byte & 0xf
        id_length = ((framing_byte >> 4) & 0x3) + 2

        if len(rx_bytes) != total_length:
            return None, None

        id_bytes = rx_bytes[:id_length]

        first = id_bytes.pop(0)
        is_extended = first & (1 << 6)
        id_value = first & 0x3f

        shift = 6
        while id_bytes:
            id_value |= (id_bytes.pop(0) << shift)
            shift += 7

        carry = rx_bytes.pop()
        to_decode = rx_bytes[id_length:]

        decoded = []

        carry |= (framing_byte & (1 << 6)) << 1

        while to_decode:
            decoded.insert(0, to_decode.pop() | (carry & (1 << 7)))
            carry <<= 1

        return id_value, decoded

    def worker(self):
        while True:
            while not self.is_end_of_frame():
                pass

            ident, data = self.decode_frame()
            if ident is None:
                continue

            diff_spec = self.diff_with_last(ident, data)
            if diff_spec is None:
                continue
            self.queue.put((ident, data, diff_spec))
            self.cache_state[ident] = data


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
        text_elements.append(f"{key:>4x}")
        for value, changed in zip(data, diff_spec):
            if now > (time_written + 2):
                changed = False
            text_elements.append(" ")
            if changed:
                text_elements.append(("red", f"{value:>02x}"))
            else:
                text_elements.append(("default", f"{value:>02x}"))

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
        ident, data, diff_spec = text_queue.get()
        VISIBLE_DATA[ident] = (data, diff_spec, time.time())
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
