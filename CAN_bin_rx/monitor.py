#!/usr/bin/env python3

import sys
import serial
from PySide6.QtWidgets import QApplication, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
from PySide6.QtCore import QTimer, Qt


class SerialPortReader(QWidget):
    def __init__(self, port):
        super().__init__()
        self.port = port
        self.id_dict = {}
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
        line = self.port.readline().decode().strip()
        fields = line.split(' ')
        if len(fields) > 0:
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
    ser = serial.Serial('/dev/ttyACM0')

    # Initialize Qt application
    app = QApplication(sys.argv)

    # Initialize serial port reader
    reader = SerialPortReader(ser)

    # Set up timer to read from serial port every 10 ms
    timer = QTimer()
    timer.timeout.connect(reader.process_serial_data)
    timer.start(500)

    # Show window
    reader.show()

    # Run Qt event loop
    sys.exit(app.exec())

    # Close serial port
    ser.close()

