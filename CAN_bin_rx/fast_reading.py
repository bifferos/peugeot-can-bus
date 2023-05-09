#!/usr/bin/env python3

import serial


reading_frame = []


def is_end_of_frame(port):
    reading_frame.append(port.read()[0])
    if (reading_frame[-1] & (1 << 7)) != 0:
        return True
    return False


def decode_frame():
    """Ignoring the final byte (start of the next frame) extract the data"""
    rx_bytes = [_ for _ in reading_frame]
    reading_frame.clear()

    framing_byte = rx_bytes[-1]
    data_length = framing_byte & 0xf
    id_length = ((framing_byte >> 4) & 0x3) + 1

    expected_length = data_length + id_length + 2 + 1

    if len(rx_bytes) != expected_length:
        return None

    bin1 = rx_bytes[-3]
    bin2 = rx_bytes[-2]

    to_decode = rx_bytes[:(data_length + id_length)]

    decoded = []

    bin_count = 0
    while to_decode:
        next_byte = to_decode.pop(0)
        if bin_count < 7:
            setting = bin1 & (1 << bin_count)
        else:
            setting = bin2 & (1 << (bin_count - 7))
        if setting:
            next_byte |= (1 << 7)
        decoded.append(next_byte)
        bin_count += 1

    data = decoded[:data_length]
    id_bits = decoded[data_length:]

    id_out = 0
    id_shift = 0
    while id_bits:
        id_out |= (id_bits.pop(0) << id_shift)
        id_shift += 8

    print(id_out, data)


def main():

    port = serial.Serial("/dev/ttyACM0", baudrate=115200)
    while True:
        while not is_end_of_frame(port):
            pass

        data = decode_frame()
        if data is None:
            continue


if __name__ == "__main__":

    main()
