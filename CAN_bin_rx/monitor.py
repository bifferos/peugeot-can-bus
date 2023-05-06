#!/usr/bin/env python3

import sys
import serial
from PySide6.QtWidgets import QApplication, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
from PySide6.QtCore import QTimer, Qt
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
            line = self.port.readline().decode().strip()
            parts = line.split(" ")
            if self.verify(parts):
                if not self.has_value(parts):
                    self.queue.put(parts)
                    self.current_state[parts[0]] = parts


class Monitor(QWidget):
    def __init__(self, reader):
        super().__init__()
        self.reader = reader
        self.id_dict = {}
        self.table = None
        self.init_ui()
        self.id_dict.clear()

    def init_ui(self):
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(['ID', 'Data'])
        self.table.verticalHeader().setVisible(False)
        layout = QVBoxLayout(self)
        layout.addWidget(self.table)
        self.setLayout(layout)
        self.setWindowTitle('CAN-BUS inspection tool')

    def process_serial_data(self):
        while not self.reader.queue.empty():
            fields = self.reader.queue.get()
            id = fields[0]
            data = ' '.join(fields[2:])
            if id in self.id_dict:
                row = self.id_dict[id]
                self.table.setItem(row, 1, QTableWidgetItem(data))
            else:
                row = self.table.rowCount()
                self.table.setRowCount(row + 1)
                self.table.setItem(row, 0, QTableWidgetItem(id))
                self.table.setItem(row, 1, QTableWidgetItem(data))
                self.id_dict[id] = row
                self.table.sortItems(0, order=Qt.AscendingOrder)


if __name__ == '__main__':
    # Open serial port
    reader = PortReader('/dev/ttyACM0')

    # Initialize Qt application
    app = QApplication(sys.argv)

    # Initialize serial port reader
    reader = Monitor(reader)

    # Set up timer to read from queue every 100 ms
    timer = QTimer()
    timer.timeout.connect(reader.process_serial_data)
    timer.start(100)

    # Show window
    reader.show()

    # Run Qt event loop
    sys.exit(app.exec())

