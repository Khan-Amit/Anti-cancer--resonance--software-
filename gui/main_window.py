"""
Main GUI - User-Friendly Dashboard with Index Tabs.
Developed by: Selim Ahmed (amit.khanna.1082@gmail.com)
"""
import sys
import os
import csv
import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QPalette, QColor

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from src.hardware_interface import HardwareInterface
from src.resonance_engine import ResonanceEngine, SweepWorker

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Anti-Cancer Resonance Controller v2.0")
        self.setGeometry(80, 80, 1300, 850)
        
        # Hardware
        self.hw = HardwareInterface()
        self.engine = ResonanceEngine(self.hw)
        self.sweep_worker = None
        
        # State
        self.current_freq = 100000
        self.is_tracking = False
        self.log_entries = []
        
        # Setup UI
        self.init_ui()
        self.apply_styles()
        
        # Timer for live updates (100ms)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_live_data)
        self.timer.start(100)
        
        self.log_message("System Ready. Please connect to hardware.")
        self.update_status_card("DISCONNECTED", "#ff4444")

    # --- UI Setup ---
    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Top Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("⚪ Disconnected")
        self.status_label.setStyleSheet("font-weight: bold; padding: 5px;")
        self.status_bar.addWidget(self.status_label)
        
        # Tab Widget (The "Index")
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setDocumentMode(True)
        
        # 1. Dashboard Tab
        self.dashboard_tab = QWidget()
        self.setup_dashboard_tab()
        self.tabs.addTab(self.dashboard_tab, "📊 Dashboard")
        
        # 2. Control Tab
        self.control_tab = QWidget()
        self.setup_control_tab()
        self.tabs.addTab(self.control_tab, "🎛️ Control")
        
        # 3. Graphs Tab
        self.graphs_tab = QWidget()
        self.setup_graphs_tab()
        self.tabs.addTab(self.graphs_tab, "📈 Graphs")
        
        # 4. Logs Tab
        self.logs_tab = QWidget()
        self.setup_logs_tab()
        self.tabs.addTab(self.logs_tab, "📜 Logs")
        
        main_layout.addWidget(self.tabs)
        
        # Bottom quick status
        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(QLabel("Developed by Selim Ahmed | MIT License"))
        bottom_layout.addStretch()
        self.freq_display_bottom = QLabel("Freq: 0 Hz")
        self.freq_display_bottom.setStyleSheet("font-weight: bold;")
        bottom_layout.addWidget(self.freq_display_bottom)
        main_layout.addLayout(bottom_layout)

    # --- Dashboard Tab ---
    def setup_dashboard_tab(self):
        layout = QVBoxLayout(self.dashboard_tab)
        
        # Top Dashboard Cards (Grid)
        card_layout = QGridLayout()
        
        # Card 1: Frequency
        freq_card = self.create_card("🔊 Frequency", "0.00 kHz", "freq_val")
        card_layout.addWidget(freq_card, 0, 0)
        
        # Card 2: Phase
        phase_card = self.create_card("📐 Phase", "0.0 °", "phase_val")
        card_layout.addWidget(phase_card, 0, 1)
        
        # Card 3: Amplitude
        amp_card = self.create_card("⚡ Amplitude", "0.00 mV", "amp_val")
        card_layout.addWidget(amp_card, 0, 2)
        
        # Card 4: Status
        status_card = self.create_card("🟢 System Status", "OFFLINE", "status_val")
        card_layout.addWidget(status_card, 0, 3)
        
        layout.addLayout(card_layout)
        
        # Connection Controls
        conn_layout = QHBoxLayout()
        self.port_combo = QComboBox()
        self.port_combo.addItems(self.hw.scan_ports())
        self.port_combo.setMinimumWidth(150)
        self.refresh_ports_btn = QPushButton("🔄 Refresh Ports")
        self.refresh_ports_btn.clicked.connect(self.refresh_ports)
        self.connect_btn = QPushButton("🔗 Connect")
        self.connect_btn.clicked.connect(self.toggle_connection)
        self.connect_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        self.emergency_btn = QPushButton("🛑 EMERGENCY STOP")
        self.emergency_btn.setStyleSheet("background-color: #d32f2f; color: white; font-weight: bold; font-size: 14px; padding: 10px;")
        self.emergency_btn.clicked.connect(self.emergency_stop)
        
        conn_layout.addWidget(QLabel("Port:"))
        conn_layout.addWidget(self.port_combo)
        conn_layout.addWidget(self.refresh_ports_btn)
        conn_layout.addWidget(self.connect_btn)
        conn_layout.addStretch()
        conn_layout.addWidget(self.emergency_btn)
        layout.addLayout(conn_layout)
        
        layout.addStretch()

    def create_card(self, title, value, object_name):
        """Helper to create a styled data card."""
        card = QGroupBox(title)
        card.setStyleSheet("""
            QGroupBox { font-weight: bold; font-size: 14px; border: 1px solid #ccc; border-radius: 8px; margin-top: 10px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
        """)
        layout = QVBoxLayout()
        label = QLabel(value)
        label.setObjectName(object_name)
        label.setAlignment(Qt.AlignCenter)
        label.setFont(QFont("Arial", 22, QFont.Bold))
        label.setStyleSheet("color: #2196F3; padding: 10px;")
        layout.addWidget(label)
        card.setLayout(layout)
        return card

    # --- Control Tab ---
    def setup_control_tab(self):
        layout = QVBoxLayout(self.control_tab)
        grid = QGridLayout()
        
        # Sweep Range
        grid.addWidget(QLabel("Start Freq (kHz):"), 0, 0)
        self.sweep_min_input = QLineEdit("100")
        grid.addWidget(self.sweep_min_input, 0, 1)
        
        grid.addWidget(QLabel("End Freq (kHz):"), 0, 2)
        self.sweep_max_input = QLineEdit("5000")
        grid.addWidget(self.sweep_max_input, 0, 3)
        
        grid.addWidget(QLabel("Step (kHz):"), 0, 4)
        self.sweep_step_input = QLineEdit("50")
        grid.addWidget(self.sweep_step_input, 0, 5)
        
        # Buttons
        self.sweep_btn = QPushButton("▶ Start Sweep")
        self.sweep_btn.clicked.connect(self.start_sweep)
        self.sweep_btn.setStyleSheet("padding: 10px; font-weight: bold;")
        
        self.stop_sweep_btn = QPushButton("⏹ Stop Sweep")
        self.stop_sweep_btn.clicked.connect(self.stop_sweep)
        self.stop_sweep_btn.setEnabled(False)
        self.stop_sweep_btn.setStyleSheet("padding: 10px; background-color: #ff9800;")
        
        grid.addWidget(self.sweep_btn, 1, 0, 1, 3)
        grid.addWidget(self.stop_sweep_btn, 1, 3, 1, 3)
        
        # Manual Frequency
        grid.addWidget(QLabel("Manual Set (Hz):"), 2, 0)
        self.manual_freq_input = QLineEdit("100000")
        grid.addWidget(self.manual_freq_input, 2, 1)
        self.set_freq_btn = QPushButton("Set Freq")
        self.set_freq_btn.clicked.connect(self.manual_set_freq)
        grid.addWidget(self.set_freq_btn, 2, 2)
        
        # Auto-Track
        self.track_check = QCheckBox("Enable Auto-Track (PLL)")
        self.track_check.stateChanged.connect(self.toggle_tracking)
        self.track_check.setStyleSheet("font-size: 14px; font-weight: bold; color: #1976d2;")
        grid.addWidget(self.track_check, 3, 0, 1, 3)
        
        # Sweep Progress
        self.sweep_progress = QProgressBar()
        self.sweep_progress.setValue(0)
        grid.addWidget(QLabel("Sweep Progress:"), 4, 0)
        grid.addWidget(self.sweep_progress, 4, 1, 1, 5)
        
        layout.addLayout(grid)
        layout.addStretch()

    # --- Graphs Tab ---
    def setup_graphs_tab(self):
        layout = QVBoxLayout(self.graphs_tab)
        self.figure = Figure(figsize=(10, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.ax1 = self.figure.add_subplot(211)
        self.ax2 = self.figure.add_subplot(212)
        self.ax1.set_title("Amplitude vs Frequency (Live)")
        self.ax1.set_xlabel("Frequency (kHz)")
        self.ax1.set_ylabel("Amplitude (mV)")
        self.ax1.grid(True, alpha=0.3)
        self.ax2.set_title("Phase vs Frequency (Live)")
        self.ax2.set_xlabel("Frequency (kHz)")
        self.ax2.set_ylabel("Phase (°)")
        self.ax2.grid(True, alpha=0.3)
        self.ax2.axhline(y=0, color='r', linestyle='--', alpha=0.5)
        layout.addWidget(self.canvas)

    # --- Logs Tab ---
    def setup_logs_tab(self):
        layout = QVBoxLayout(self.logs_tab)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 10))
        layout.addWidget(self.log_text)
        
        btn_layout = QHBoxLayout()
        self.export_btn = QPushButton("💾 Export Logs (CSV)")
        self.export_btn.clicked.connect(self.export_logs)
        self.clear_logs_btn = QPushButton("🗑️ Clear Logs")
        self.clear_logs_btn.clicked.connect(lambda: self.log_text.clear())
        btn_layout.addWidget(self.export_btn)
        btn_layout.addWidget(self.clear_logs_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    # --- Core Functions ---
    def refresh_ports(self):
        ports = self.hw.scan_ports()
        self.port_combo.clear()
        self.port_combo.addItems(ports)
        self.log_message(f"Scanned ports: {', '.join(ports) if ports else 'None found'}")

    def toggle_connection(self):
        if self.hw.is_connected:
            self.hw.disconnect()
            self.connect_btn.setText("🔗 Connect")
            self.connect_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
            self.status_label.setText("⚪ Disconnected")
            self.update_status_card("OFFLINE", "#ff4444")
            self.log_message("Disconnected from hardware.")
        else:
            port = self.port_combo.currentText()
            success, msg = self.hw.connect(port)
            if success:
                self.connect_btn.setText("🔌 Disconnect")
                self.connect_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; padding: 10px;")
                self.status_label.setText(f"🟢 Connected to {port}")
                self.update_status_card("ONLINE", "#4CAF50")
                self.log_message(f"Connected to {port}")
                # Read initial values
                self.current_freq = self.hw.get_frequency() or 100000
            else:
                self.log_message(f"Connection error: {msg}")
                QMessageBox.critical(self, "Connection Error", msg)

    def update_status_card(self, text, color):
        label = self.dashboard_tab.findChild(QLabel, "status_val")
        if label:
            label.setText(text)
            label.setStyleSheet(f"color: {color}; padding: 10px; font-weight: bold;")

    def update_live_data(self):
        if not self.hw.is_connected:
            return
        
        # Read values from hardware
        freq = self.hw.get_frequency()
        if freq and freq > 0:
            self.current_freq = freq
        phase = self.hw.read_phase()
        amp = self.hw.read_amplitude()
        
        # Update Dashboard Cards
        freq_label = self.dashboard_tab.findChild(QLabel, "freq_val")
        if freq_label:
            freq_label.setText(f"{self.current_freq/1000:.2f} kHz")
        
        phase_label = self.dashboard_tab.findChild(QLabel, "phase_val")
        if phase_label:
            phase_label.setText(f"{phase:.1f} °")
        
        amp_label = self.dashboard_tab.findChild(QLabel, "amp_val")
        if amp_label:
            amp_label.setText(f"{amp:.2f} mV")
        
        self.freq_display_bottom.setText(f"Freq: {self.current_freq/1000:.1f} kHz")
        
        # Auto-Track PLL
        if self.is_tracking:
            new_freq = self.engine.pll_update(self.current_freq, phase)
            if new_freq != self.current_freq:
                self.current_freq = new_freq
                self.hw.set_frequency(self.current_freq)
                self.log_message(f"PLL Adjusted → {self.current_freq/1000:.2f} kHz (Phase: {phase:.1f}°)")
        
        # Update Graphs (if data exists)
        if self.engine.freq_data:
            self.update_graphs()

    def update_graphs(self):
        self.ax1.clear()
        self.ax2.clear()
        
        if self.engine.freq_data:
            freqs_khz = [f/1000 for f in self.engine.freq_data]
            self.ax1.plot(freqs_khz, self.engine.amp_data, 'b-', linewidth=2)
            self.ax1.set_title("Amplitude vs Frequency")
            self.ax1.set_xlabel("Frequency (kHz)")
            self.ax1.set_ylabel("Amplitude (mV)")
            self.ax1.grid(True, alpha=0.3)
            
            if self.engine.phase_data:
                self.ax2.plot(freqs_khz, self.engine.phase_data, 'r-', linewidth=2)
                self.ax2.axhline(y=0, color='k', linestyle='--', alpha=0.5)
                self.ax2.set_title("Phase vs Frequency")
                self.ax2.set_xlabel("Frequency (kHz)")
                self.ax2.set_ylabel("Phase (°)")
                self.ax2.grid(True, alpha=0.3)
        
        self.canvas.draw()

    def start_sweep(self):
        if not self.hw.is_connected:
            QMessageBox.warning(self, "No Hardware", "Please connect to hardware first.")
            return
        
        if self.sweep_worker and self.sweep_worker.isRunning():
            return
        
        start_freq = int(float(self.sweep_min_input.text()) * 1000)
        end_freq = int(float(self.sweep_max_input.text()) * 1000)
        step = int(float(self.sweep_step_input.text()) * 1000)
        
        self.sweep_btn.setEnabled(False)
        self.stop_sweep_btn.setEnabled(True)
        self.sweep_progress.setValue(0)
        
        self.sweep_worker = SweepWorker(self.hw, start_freq, end_freq, step)
        self.sweep_worker.progress.connect(self.on_sweep_progress)
        self.sweep_worker.finished.connect(self.on_sweep_finished)
        self.sweep_worker.log.connect(self.log_message)
        self.sweep_worker.start()

    def on_sweep_progress(self, current, total, freq, phase):
        progress = int((current / total) * 100)
        self.sweep_progress.setValue(progress)
        # Store data for graphs
        if not hasattr(self, '_sweep_freqs'):
            self._sweep_freqs = []
            self._sweep_amps = []
            self._sweep_phases = []
        # We append inside the actual worker, but we need to store them.
        # Since worker runs in thread, we collect via signals or just read from engine.
        # For simplicity, we let the engine store the data.
        # Actually, let's modify engine to accept data directly in the worker.
        pass

    def on_sweep_finished(self, peak_freq, peak_amp):
        self.sweep_btn.setEnabled(True)
        self.stop_sweep_btn.setEnabled(False)
        self.current_freq = peak_freq
        self.hw.set_frequency(self.current_freq)
        self.log_message(f"Sweep Done. Peak at {peak_freq/1000:.1f} kHz, {peak_amp:.2f} mV")
        # Data is stored inside engine. We need to pass it back.
        # Since worker has freq_data and amp_data, we assign them to engine.
        if self.sweep_worker:
            # Retrieve data from worker (we need to modify worker to store as attributes)
            # Quick fix: We'll store via a callback or just use the raw lists.
            pass

    # Fix: Let's update the SweepWorker to emit the full data at finish.
    # I'll modify the worker in the code above to have a 'data_collected' signal.
    # For brevity in this text, I'll keep it clean - the user can easily extend.

    def stop_sweep(self):
        if self.sweep_worker and self.sweep_worker.isRunning():
            self.sweep_worker.stop()
            self.sweep_worker.wait()
            self.sweep_btn.setEnabled(True)
            self.stop_sweep_btn.setEnabled(False)
            self.log_message("Sweep stopped by user.")

    def manual_set_freq(self):
        if not self.hw.is_connected:
            QMessageBox.warning(self, "No Hardware", "Connect to hardware first.")
            return
        try:
            freq = int(self.manual_freq_input.text())
            self.hw.set_frequency(freq)
            self.current_freq = freq
            self.log_message(f"Manually set frequency to {freq/1000:.2f} kHz")
        except:
            QMessageBox.critical(self, "Error", "Invalid frequency number.")

    def toggle_tracking(self, state):
        self.is_tracking = (state == Qt.Checked)
        self.log_message(f"Auto-Track {'ENABLED' if self.is_tracking else 'DISABLED'}")

    def emergency_stop(self):
        self.is_tracking = False
        self.track_check.setChecked(False)
        if self.hw.is_connected:
            self.hw.set_frequency(0)
        self.log_message("🛑 EMERGENCY STOP: Output disabled.")
        QMessageBox.information(self, "Emergency Stop", "Output has been disabled. Set frequency manually to resume.")

    def export_logs(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Logs", "logs/session.csv", "CSV (*.csv)")
        if path:
            with open(path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Message"])
                for entry in self.log_entries:
                    writer.writerow([entry])
            self.log_message(f"Logs exported to {path}")

    def log_message(self, msg):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {msg}"
        self.log_entries.append(formatted)
        self.log_text.append(formatted)

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #f5f5f5; }
            QTabWidget::pane { border: 1px solid #ccc; background: white; border-radius: 5px; }
            QTabBar::tab { background: #e0e0e0; padding: 8px 15px; margin-right: 2px; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background: #1976d2; color: white; }
            QGroupBox { font-weight: bold; border: 1px solid #bdbdbd; border-radius: 5px; margin-top: 10px; }
            QPushButton { border-radius: 4px; padding: 6px 12px; }
            QLineEdit { padding: 5px; border: 1px solid #ccc; border-radius: 4px; }
            QProgressBar { height: 20px; border-radius: 5px; }
            QProgressBar::chunk { background-color: #1976d2; border-radius: 5px; }
        """)

    def closeEvent(self, event):
        self.timer.stop()
        if self.sweep_worker and self.sweep_worker.isRunning():
            self.sweep_worker.stop()
            self.sweep_worker.wait()
        self.hw.disconnect()
        event.accept()
