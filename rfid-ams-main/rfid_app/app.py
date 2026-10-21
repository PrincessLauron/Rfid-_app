import os
import sys
from dataclasses import dataclass
from typing import Optional, List

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QSpinBox,
    QListWidget,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from .serial_manager import SerialManager, TagRead
from .ingest_client import IngestClient
from .sync_worker import SyncWorker


@dataclass
class AppConfig:
    api_base_url: str = os.getenv("AMS_API_BASE_URL", "http://127.0.0.1:8000")
    api_token: Optional[str] = os.getenv("AMS_API_TOKEN")  # optional bearer token
    serial_port: str = os.getenv("AMS_SERIAL_PORT", "/dev/ttyUSB0")
    baudrate: int = int(os.getenv("AMS_BAUDRATE", "115200"))


class SerialWorker(QThread):
    tag_read_signal = pyqtSignal(object)  # TagRead
    status_signal = pyqtSignal(str)

    def __init__(self, manager: SerialManager):
        super().__init__()
        self.manager = manager
        self._running = False

    def run(self):
        self._running = True
        for event in self.manager.read_loop():
            if not self._running:
                break
            if isinstance(event, TagRead):
                self.tag_read_signal.emit(event)
            elif isinstance(event, str):
                self.status_signal.emit(event)

    def stop(self):
        self._running = False
        self.manager.stop()
        self.wait(1000)


class MainWindow(QMainWindow):
    def __init__(self, config: AppConfig):
        super().__init__()
        self.setWindowTitle("RFID AMS - Control")
        self.config = config
        self.manager = SerialManager(self.config.serial_port, self.config.baudrate)
        self.ingest = IngestClient(self.config.api_base_url, self.config.api_token)
        self.sync = SyncWorker(self.ingest, interval_seconds=10)
        self.worker: Optional[SerialWorker] = None

        self._build_ui()

    def _build_ui(self):
        root = QWidget()
        layout = QVBoxLayout()

        # Status row
        status_row = QHBoxLayout()
        self.status_label = QLabel("Disconnected")
        status_row.addWidget(QLabel("Status:"))
        status_row.addWidget(self.status_label, 1)
        layout.addLayout(status_row)

        # Controls row
        controls = QHBoxLayout()
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.on_connect)
        controls.addWidget(self.connect_btn)
        self.start_btn = QPushButton("Start Scan")
        self.start_btn.clicked.connect(self.on_start)
        controls.addWidget(self.start_btn)
        self.stop_btn = QPushButton("Stop Scan")
        self.stop_btn.clicked.connect(self.on_stop)
        controls.addWidget(self.stop_btn)
        layout.addLayout(controls)

        # Power control
        power_row = QHBoxLayout()
        power_row.addWidget(QLabel("Power (dBm):"))
        self.power_spin = QSpinBox()
        self.power_spin.setRange(5, 30)
        self.power_spin.setValue(20)
        power_row.addWidget(self.power_spin)
        self.set_power_btn = QPushButton("Set Power")
        self.set_power_btn.clicked.connect(self.on_set_power)
        power_row.addWidget(self.set_power_btn)
        layout.addLayout(power_row)

        # Inventory mode
        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Inventory Mode:"))
        self.mode_input = QLineEdit()
        self.mode_input.setPlaceholderText("single / continuous")
        mode_row.addWidget(self.mode_input)
        self.set_mode_btn = QPushButton("Set Mode")
        self.set_mode_btn.clicked.connect(self.on_set_mode)
        mode_row.addWidget(self.set_mode_btn)
        layout.addLayout(mode_row)

        # Live tag list
        self.tag_list = QListWidget()
        layout.addWidget(QLabel("Live Tag Reads"))
        layout.addWidget(self.tag_list, 1)

        root.setLayout(layout)
        self.setCentralWidget(root)
        self.resize(720, 480)

    def on_connect(self):
        ok, msg = self.manager.connect()
        self.status_label.setText(msg)
        if ok:
            self.sync.start()

    def on_start(self):
        if self.worker and self.worker.isRunning():
            return
        self.worker = SerialWorker(self.manager)
        self.worker.tag_read_signal.connect(self.on_tag_read)
        self.worker.status_signal.connect(self.on_status)
        self.worker.start()
        self.status_label.setText("Scanning...")

    def on_stop(self):
        if self.worker:
            self.worker.stop()
            self.worker = None
        self.status_label.setText("Stopped")
        self.sync.stop()

    def on_set_power(self):
        value = int(self.power_spin.value())
        self.manager.set_power(value)
        self.status_label.setText(f"Power set to {value} dBm")

    def on_set_mode(self):
        mode = self.mode_input.text().strip() or "single"
        self.manager.set_mode(mode)
        self.status_label.setText(f"Mode set to {mode}")

    def on_tag_read(self, tag: TagRead):
        self.tag_list.insertItem(0, f"{tag.epc}  RSSI:{tag.rssi or ''}")
        self.ingest.send_tag_read(tag)

    def on_status(self, message: str):
        self.status_label.setText(message)


def main():
    app = QApplication(sys.argv)
    window = MainWindow(AppConfig())
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()


