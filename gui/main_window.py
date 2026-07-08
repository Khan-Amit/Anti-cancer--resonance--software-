"""
Main GUI - User-Friendly Dashboard with Treatment Planner (Front End Index).
Developed by: Selim Ahmed (amit.khanna.1082@gmail.com)
"""
import sys
import os
import csv
import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QPalette, QColor, QTextCursor

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from src.hardware_interface import HardwareInterface
from src.resonance_engine import ResonanceEngine, SweepWorker

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Anti-Cancer Resonance Controller v3.0 - Treatment Planner")
        self.setGeometry(50, 50, 1400, 900)
        
        # Hardware
        self.hw = HardwareInterface()
        self.engine = ResonanceEngine(self.hw)
        self.sweep_worker = None
        
        # State
        self.current_freq = 100000
        self.is_tracking = False
        self.log_entries = []
        self.sweep_results = None  # Store latest sweep peak
        
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
        
        # 2. TREATMENT PLANNER (NEW FRONT END INDEX)
        self.planner_tab = QWidget()
        self.setup_planner_tab()
        self.tabs.addTab(self.planner_tab, "📋 Treatment Planner")
        
        # 3. Control Tab
        self.control_tab = QWidget()
        self.setup_control_tab()
        self.tabs.addTab(self.control_tab, "🎛️ Manual Control")
        
        # 4. Graphs Tab
        self.graphs_tab = QWidget()
        self.setup_graphs_tab()
        self.tabs.addTab(self.graphs_tab, "📈 Graphs")
        
        # 5. Logs Tab
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

    # ============================================================
    # 1. DASHBOARD TAB
    # ============================================================
    def setup_dashboard_tab(self):
        layout = QVBoxLayout(self.dashboard_tab)
        
        card_layout = QGridLayout()
        freq_card = self.create_card("🔊 Frequency", "0.00 kHz", "freq_val")
        card_layout.addWidget(freq_card, 0, 0)
        phase_card = self.create_card("📐 Phase", "0.0 °", "phase_val")
        card_layout.addWidget(phase_card, 0, 1)
        amp_card = self.create_card("⚡ Amplitude", "0.00 mV", "amp_val")
        card_layout.addWidget(amp_card, 0, 2)
        status_card = self.create_card("🟢 System Status", "OFFLINE", "status_val")
        card_layout.addWidget(status_card, 0, 3)
        layout.addLayout(card_layout)
        
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
        card = QGroupBox(title)
        card.setStyleSheet("""QGroupBox { font-weight: bold; font-size: 14px; border: 1px solid #ccc; border-radius: 8px; margin-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }""")
        layout = QVBoxLayout()
        label = QLabel(value)
        label.setObjectName(object_name)
        label.setAlignment(Qt.AlignCenter)
        label.setFont(QFont("Arial", 22, QFont.Bold))
        label.setStyleSheet("color: #2196F3; padding: 10px;")
        layout.addWidget(label)
        card.setLayout(layout)
        return card

    # ============================================================
    # 2. TREATMENT PLANNER (FRONT END INDEX)
    # ============================================================
    def setup_planner_tab(self):
        layout = QVBoxLayout(self.planner_tab)
        
        # Top: Patient Info Grid
        patient_group = QGroupBox("👤 Patient & Tumor Parameters")
        patient_layout = QGridLayout()
        
        # Row 0
        patient_layout.addWidget(QLabel("Patient Name:"), 0, 0)
        self.patient_name = QLineEdit("John Doe")
        patient_layout.addWidget(self.patient_name, 0, 1)
        
        patient_layout.addWidget(QLabel("Patient ID:"), 0, 2)
        self.patient_id = QLineEdit("P-001")
        patient_layout.addWidget(self.patient_id, 0, 3)
        
        # Row 1
        patient_layout.addWidget(QLabel("Tumor Type:"), 1, 0)
        self.tumor_type = QComboBox()
        self.tumor_type.addItems(["Liver", "Pancreas", "Breast", "Brain (GBM)", "Lung", "Skin/Melanoma"])
        patient_layout.addWidget(self.tumor_type, 1, 1)
        
        patient_layout.addWidget(QLabel("Depth (cm):"), 1, 2)
        self.tumor_depth = QLineEdit("3.5")
        patient_layout.addWidget(self.tumor_depth, 1, 3)
        
        patient_layout.addWidget(QLabel("Size (mm):"), 1, 4)
        self.tumor_size = QLineEdit("25")
        patient_layout.addWidget(self.tumor_size, 1, 5)
        
        patient_group.setLayout(patient_layout)
        layout.addWidget(patient_group)

        # Middle: Auto-Calc & Instructions
        calc_group = QGroupBox("⚙️ Auto-Calculation & SOP Generation")
        calc_layout = QVBoxLayout()
        
        # Buttons for Auto-Calc
        btn_layout = QHBoxLayout()
        self.auto_calc_btn = QPushButton("🧮 Auto-Calculate Frequencies & Instructions")
        self.auto_calc_btn.clicked.connect(self.auto_calculate_plan)
        self.auto_calc_btn.setStyleSheet("background-color: #1976d2; color: white; font-weight: bold; padding: 8px;")
        btn_layout.addWidget(self.auto_calc_btn)
        btn_layout.addStretch()
        calc_layout.addLayout(btn_layout)
        
        # Display Calculated Parameters
        params_layout = QHBoxLayout()
        self.calc_start_label = QLabel("Start: 100.0 kHz")
        self.calc_start_label.setStyleSheet("font-weight: bold; color: #2e7d32;")
        self.calc_end_label = QLabel("End: 500.0 kHz")
        self.calc_end_label.setStyleSheet("font-weight: bold; color: #c62828;")
        self.calc_step_label = QLabel("Step: 10.0 kHz")
        self.calc_step_label.setStyleSheet("font-weight: bold;")
        params_layout.addWidget(self.calc_start_label)
        params_layout.addWidget(self.calc_end_label)
        params_layout.addWidget(self.calc_step_label)
        params_layout.addStretch()
        calc_layout.addLayout(params_layout)
        
        # SOP Instructions Box
        self.sop_text = QTextEdit()
        self.sop_text.setReadOnly(True)
        self.sop_text.setPlaceholderText("Click 'Auto-Calculate' to generate step-by-step operation instructions...")
        self.sop_text.setFont(QFont("Consolas", 10))
        self.sop_text.setMinimumHeight(150)
        calc_layout.addWidget(QLabel("📄 Generated Operation Instructions (SOP):"))
        calc_layout.addWidget(self.sop_text)
        
        calc_group.setLayout(calc_layout)
        layout.addWidget(calc_group)

        # Bottom: Action Buttons (The "Operation" part)
        action_group = QGroupBox("🚀 Automated Operation & Reporting")
        action_layout = QHBoxLayout()
        
        self.run_auto_btn = QPushButton("▶ Run Full Auto-Treatment")
        self.run_auto_btn.clicked.connect(self.run_auto_treatment)
        self.run_auto_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; font-size: 14px; padding: 15px;")
        action_layout.addWidget(self.run_auto_btn)
        
        self.generate_report_btn = QPushButton("📄 Generate Patient Report")
        self.generate_report_btn.clicked.connect(self.generate_patient_report)
        self.generate_report_btn.setStyleSheet("background-color: #ff9800; color: white; font-weight: bold; padding: 15px;")
        action_layout.addWidget(self.generate_report_btn)
        
        self.clear_plan_btn = QPushButton("🗑️ Clear Plan")
        self.clear_plan_btn.clicked.connect(self.clear_plan)
        action_layout.addWidget(self.clear_plan_btn)
        
        action_group.setLayout(action_layout)
        layout.addWidget(action_group)

    # ============================================================
    # PLANNER LOGIC
    # ============================================================
    def auto_calculate_plan(self):
        """Calculates optimal frequencies based on tumor type/depth and generates SOP."""
        try:
            depth = float(self.tumor_depth.text())
            tumor = self.tumor_type.currentText()
        except:
            QMessageBox.critical(self, "Error", "Invalid depth value.")
            return

        # --- Auto-Calculation Algorithm ---
        # Base frequencies on tissue depth (deeper = lower freq for penetration)
        if "Brain" in tumor:
            start_khz, end_khz = 150, 500
        elif "Liver" in tumor or "Pancreas" in tumor:
            start_khz, end_khz = 80, 300
        elif "Breast" in tumor or "Skin" in tumor:
            start_khz, end_khz = 500, 1500
        else:  # Lung or others
            start_khz, end_khz = 100, 400
            
        # Adjust for depth (deeper = shift lower)
        if depth > 5.0:
            start_khz = max(50, start_khz - 50)
            end_khz = max(200, end_khz - 100)
        elif depth < 2.0:
            start_khz = min(800, start_khz + 200)
            end_khz = min(3000, end_khz + 500)
            
        # Calculate adaptive step
        step_khz = max(5, int((end_khz - start_khz) / 30))

        # Update UI Labels
        self.calc_start_label.setText(f"Start: {start_khz:.1f} kHz")
        self.calc_end_label.setText(f"End: {end_khz:.1f} kHz")
        self.calc_step_label.setText(f"Step: {step_khz:.1f} kHz")
        
        # Store for later use
        self._plan_start = int(start_khz * 1000)
        self._plan_end = int(end_khz * 1000)
        self._plan_step = int(step_khz * 1000)

        # --- Generate SOP Instructions ---
        sop = f"""
=== STANDARD OPERATING PROCEDURE (SOP) ===
Patient: {self.patient_name.text()} (ID: {self.patient_id.text()})
Tumor: {tumor} | Depth: {depth} cm | Size: {self.tumor_size.text()} mm

AUTO-CALCULATED PARAMETERS:
1. Frequency Range: {start_khz:.1f} kHz to {end_khz:.1f} kHz
2. Sweep Step: {step_khz:.1f} kHz
3. Total Steps: {int((end_khz - start_khz) / step_khz)}

OPERATOR INSTRUCTIONS:
1. Ensure hardware is connected (Port: {self.port_combo.currentText()}).
2. Click "Connect" on the Dashboard tab.
3. Click "Run Full Auto-Treatment" below to start the automated sequence.
4. The system will:
   a) Sweep through the calculated range to find the resonance peak.
   b) Automatically lock onto the optimal frequency.
   c) Enable Phase-Locked Loop (PLL) to maintain resonance.
5. Monitor Live Data Cards on the Dashboard for real-time feedback.
6. In case of emergency, press the "EMERGENCY STOP" button immediately.

TREATMENT DURATION ESTIMATE: ~{int((end_khz - start_khz) / step_khz) * 2} seconds.
"""
        self.sop_text.setText(sop)
        self.log_message("Auto-calculation complete. SOP generated.")

    def run_auto_treatment(self):
        """The 'One-Click Operation' - Automates everything."""
        if not self.hw.is_connected:
            reply = QMessageBox.question(self, "Hardware Not Connected", 
                                         "Hardware is not connected. Connect now?", 
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.toggle_connection()
                if not self.hw.is_connected:
                    return
            else:
                return
        
        # Check if we have a plan
        if not hasattr(self, '_plan_start') or self._plan_start is None:
            QMessageBox.information(self, "No Plan", "Please click 'Auto-Calculate' first.")
            return
            
        self.log_message("🚀 Starting Full Auto-Treatment Sequence...")
        self.run_auto_btn.setEnabled(False)
        self.auto_calc_btn.setEnabled(False)

        # Disable manual tracking during auto-run
        self.is_tracking = False
        self.track_check.setChecked(False)

        # Step 1: Set the starting frequency
        self.log_message(f"Step 1: Setting initial frequency to {self._plan_start/1000:.1f} kHz")
        self.hw.set_frequency(self._plan_start)
        
        # Step 2: Start Sweep (This is asynchronous, uses the SweepWorker)
        self.sweep_btn.setEnabled(False) # Disable manual sweep button
        self.sweep_worker = SweepWorker(self.hw, self._plan_start, self._plan_end, self._plan_step)
        self.sweep_worker.progress.connect(self.on_sweep_progress)
        self.sweep_worker.finished.connect(self.on_auto_sweep_finished) # Special callback
        self.sweep_worker.log.connect(self.log_message)
        self.sweep_worker.start()
        self.log_message("Step 2: Sweeping for resonance...")

    def on_auto_sweep_finished(self, peak_freq, peak_amp, freq_data, amp_data, phase_data):
        """Callback for the auto-treatment sweep."""
        # Store data in engine
        self.engine.set_sweep_data(freq_data, amp_data, phase_data)
        self.sweep_results = (peak_freq, peak_amp)
        
        self.current_freq = peak_freq
        self.hw.set_frequency(self.current_freq)
        
        self.log_message(f"✅ Step 3: Resonance locked at {peak_freq/1000:.1f} kHz (Amp: {peak_amp:.2f} mV)")
        
        # Step 4: Enable PLL
        self.is_tracking = True
        self.track_check.setChecked(True)
        self.log_message("✅ Step 4: Auto-Track (PLL) ENABLED. System is now maintaining resonance.")
        
        # Re-enable UI
        self.run_auto_btn.setEnabled(True)
        self.auto_calc_btn.setEnabled(True)
        self.sweep_btn.setEnabled(True)
        self.stop_sweep_btn.setEnabled(False)
        
        # Update graphs
        self.update_graphs()
        self.tabs.setCurrentIndex(3)  # Switch to Graphs tab to show result
        
        QMessageBox.information(self, "Auto-Treatment Complete", 
                                f"Resonance locked at {peak_freq/1000:.1f} kHz.\n"
                                f"PLL is now active. Monitor the Dashboard for live data.")

    def generate_patient_report(self):
        """Generates a detailed patient report and saves to logs."""
        if not self.sweep_results:
            QMessageBox.warning(self, "No Data", "Run a treatment or sweep first to generate a report.")
            return
            
        peak_freq, peak_amp = self.sweep_results
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""
============================================
    ANTI-CANCER RESONANCE TREATMENT REPORT
============================================
Generated: {now}
Software: ACRS v3.0 (MIT License)
Developer: Selim Ahmed

--- PATIENT INFORMATION ---
Name: {self.patient_name.text()}
ID: {self.patient_id.text()}
Tumor Type: {self.tumor_type.currentText()}
Depth: {self.tumor_depth.text()} cm
Size: {self.tumor_size.text()} mm

--- TREATMENT PARAMETERS ---
Sweep Start: {self.calc_start_label.text()}
Sweep End: {self.calc_end_label.text()}
Step Size: {self.calc_step_label.text()}
Resonant Frequency: {peak_freq/1000:.2f} kHz
Peak Amplitude: {peak_amp:.2f} mV
Auto-Track (PLL): {'Enabled' if self.is_tracking else 'Disabled'}

--- OPERATOR INSTRUCTIONS (SOP) ---
{self.sop_text.toPlainText()}

--- SYSTEM STATUS ---
Hardware: {'Connected' if self.hw.is_connected else 'Disconnected'}
Frequency Output: {self.current_freq/1000:.2f} kHz

============================================
"""
        # Save to file
        os.makedirs("logs", exist_ok=True)
        filename = f"logs/report_{self.patient_id.text()}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w') as f:
            f.write(report)
        
        self.log_message(f"📄 Report saved to {filename}")
        QMessageBox.information(self, "Report Saved", f"Report saved to:\n{filename}")
        
        # Show preview
        preview = QTextEdit()
        preview.setPlainText(report)
        preview.setWindowTitle("Patient Report Preview")
        preview.resize(800, 600)
        preview.show()

    def clear_plan(self):
        self.sop_text.clear()
        self.calc_start_label.setText("Start: ---")
        self.calc_end_label.setText("End: ---")
        self.calc_step_label.setText("Step: ---")
        if hasattr(self, '_plan_start'):
            del self._plan_start
        self.sweep_results = None
        self.log_message("Plan cleared.")

    # ============================================================
    # 3. MANUAL CONTROL TAB
    # ============================================================
    def setup_control_tab(self):
        layout = QVBoxLayout(self.control_tab)
        grid = QGridLayout()
        
        grid.addWidget(QLabel("Start Freq (kHz):"), 0, 0)
        self.sweep_min_input = QLineEdit("100")
        grid.addWidget(self.sweep_min_input, 0, 1)
        grid.addWidget(QLabel("End Freq (kHz):"), 0, 2)
        self.sweep_max_input = QLineEdit("5000")
        grid.addWidget(self.sweep_max_input, 0, 3)
        grid.addWidget(QLabel("Step (kHz):"), 0, 4)
        self.sweep_step_input = QLineEdit("50")
        grid.addWidget(self.sweep_step_input, 0, 5)
        
        self.sweep_btn = QPushButton("▶ Start Sweep")
        self.sweep_btn.clicked.connect(self.start_sweep)
        self.sweep_btn.setStyleSheet("padding: 10px; font-weight: bold;")
        self.stop_sweep_btn = QPushButton("⏹ Stop Sweep")
        self.stop_sweep_btn.clicked.connect(self.stop_sweep)
        self.stop_sweep_btn.setEnabled(False)
        self.stop_sweep_btn.setStyleSheet("padding: 10px; background-color: #ff9800;")
        grid.addWidget(self.sweep_btn, 1, 0, 1, 3)
        grid.addWidget(self.stop_sweep_btn, 1, 3, 1, 3)
        
        grid.addWidget(QLabel("Manual Set (Hz):"), 2, 0)
        self.manual_freq_input = QLineEdit("100000")
        grid.addWidget(self.manual_freq_input, 2, 1)
        self.set_freq_btn = QPushButton("Set Freq")
        self.set_freq_btn.clicked.connect(self.manual_set_freq)
        grid.addWidget(self.set_freq_btn, 2, 2)
        
        self.track_check = QCheckBox("Enable Auto-Track (PLL)")
        self.track_check.stateChanged.connect(self.toggle_tracking)
        self.track_check.setStyleSheet("font-size: 14px; font-weight: bold; color: #1976d2;")
        grid.addWidget(self.track_check, 3, 0, 1, 3)
        
        self.sweep_progress = QProgressBar()
        self.sweep_progress.setValue(0)
        grid.addWidget(QLabel("Sweep Progress:"), 4, 0)
        grid.addWidget(self.sweep_progress, 4, 1, 1, 5)
        
        layout.addLayout(grid)
        layout.addStretch()

    # ============================================================
    # 4. GRAPHS TAB
    # ============================================================
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

    # ============================================================
    # 5. LOGS TAB
    # ============================================================
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

    # ============================================================
    # CORE OPERATIONAL FUNCTIONS (Shared between Manual & Auto)
    # ============================================================
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
        freq = self.hw.get_frequency()
        if freq and freq > 0:
            self.current_freq = freq
        phase = self.hw.read_phase()
        amp = self.hw.read_amplitude()
        
        freq_label = self.dashboard_tab.findChild(QLabel, "freq_val")
        if freq_label: freq_label.setText(f"{self.current_freq/1000:.2f} kHz")
        phase_label = self.dashboard_tab.findChild(QLabel, "phase_val")
        if phase_label: phase_label.setText(f"{phase:.1f} °")
        amp_label = self.dashboard_tab.findChild(QLabel, "amp_val")
        if amp_label: amp_label.setText(f"{amp:.2f} mV")
        self.freq_display_bottom.setText(f"Freq: {self.current_freq/1000:.1f} kHz")
        
        if self.is_tracking:
            new_freq = self.engine.pll_update(self.current_freq, phase)
            if new_freq != self.current_freq:
                self.current_freq = new_freq
                self.hw.set_frequency(self.current_freq)
                self.log_message(f"PLL Adjusted → {self.current_freq/1000:.2f} kHz (Phase: {phase:.1f}°)")
        
        if self.engine.freq_data:
            self.update_graphs()

    def update_graphs(self):
        self.ax1.clear(); self.ax2.clear()
        if self.engine.freq_data:
            freqs_khz = [f/1000 for f in self.engine.freq_data]
            self.ax1.plot(freqs_khz, self.engine.amp_data, 'b-', linewidth=2)
            self.ax1.set_title("Amplitude vs Frequency"); self.ax1.set_xlabel("Frequency (kHz)"); self.ax1.set_ylabel("Amplitude (mV)"); self.ax1.grid(True, alpha=0.3)
            if self.engine.phase_data:
                self.ax2.plot(freqs_khz, self.engine.phase_data, 'r-', linewidth=2)
                self.ax2.axhline(y=0, color='k', linestyle='--', alpha=0.5)
                self.ax2.set_title("Phase vs Frequency"); self.ax2.set_xlabel("Frequency (kHz)"); self.ax2.set_ylabel("Phase (°)"); self.ax2.grid(True, alpha=0.3)
        self.canvas.draw()

    def start_sweep(self):
        if not self.hw.is_connected:
            QMessageBox.warning(self, "No Hardware", "Connect to hardware first.")
            return
        if self.sweep_worker and self.sweep_worker.isRunning(): return
        start_freq = int(float(self.sweep_min_input.text()) * 1000)
        end_freq = int(float(self.sweep_max_input.text()) * 1000)
        step = int(float(self.sweep_step_input.text()) * 1000)
        
        self.sweep_btn.setEnabled(False); self.stop_sweep_btn.setEnabled(True); self.sweep_progress.setValue(0)
        self.sweep_worker = SweepWorker(self.hw, start_freq, end_freq, step)
        self.sweep_worker.progress.connect(self.on_sweep_progress)
        self.sweep_worker.finished.connect(self.on_sweep_finished)
        self.sweep_worker.log.connect(self.log_message)
        self.sweep_worker.start()

    def on_sweep_progress(self, current, total, freq, phase):
        self.sweep_progress.setValue(int((current/total)*100))

    def on_sweep_finished(self, peak_freq, peak_amp, freq_data, amp_data, phase_data):
        self.engine.set_sweep_data(freq_data, amp_data, phase_data)
        self.sweep_results = (peak_freq, peak_amp)
        self.sweep_btn.setEnabled(True); self.stop_sweep_btn.setEnabled(False)
        self.current_freq = peak_freq; self.hw.set_frequency(self.current_freq)
        self.log_message(f"Sweep Done. Peak at {peak_freq/1000:.1f} kHz")
        self.update_graphs()

    def stop_sweep(self):
        if self.sweep_worker and self.sweep_worker.isRunning():
            self.sweep_worker.stop(); self.sweep_worker.wait()
            self.sweep_btn.setEnabled(True); self.stop_sweep_btn.setEnabled(False)
            self.log_message("Sweep stopped.")

    def manual_set_freq(self):
        if not self.hw.is_connected:
            QMessageBox.warning(self, "No Hardware", "Connect first.")
            return
        try:
            freq = int(self.manual_freq_input.text())
            self.hw.set_frequency(freq); self.current_freq = freq
            self.log_message(f"Set frequency to {freq/1000:.2f} kHz")
        except: QMessageBox.critical(self, "Error", "Invalid number.")

    def toggle_tracking(self, state):
        self.is_tracking = (state == Qt.Checked)
        self.log_message(f"Auto-Track {'ENABLED' if self.is_tracking else 'DISABLED'}")

    def emergency_stop(self):
        self.is_tracking = False; self.track_check.setChecked(False)
        if self.hw.is_connected: self.hw.set_frequency(0)
        self.log_message("🛑 EMERGENCY STOP: Output disabled.")
        QMessageBox.information(self, "Emergency Stop", "Output disabled.")

    def export_logs(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Logs", "logs/session.csv", "CSV (*.csv)")
        if path:
            with open(path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Message"])
                for entry in self.log_entries: writer.writerow([entry])
            self.log_message(f"Logs exported to {path}")

    def log_message(self, msg):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {msg}"
        self.log_entries.append(formatted)
        self.log_text.append(formatted)
        # Scroll to bottom
        self.log_text.moveCursor(QTextCursor.End)

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
            QTextEdit { border: 1px solid #ccc; border-radius: 4px; }
        """)

    def closeEvent(self, event):
        self.timer.stop()
        if self.sweep_worker and self.sweep_worker.isRunning():
            self.sweep_worker.stop(); self.sweep_worker.wait()
        self.hw.disconnect()
        event.accept()
