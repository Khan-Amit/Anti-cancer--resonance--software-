"""
ACRS v3.0 - Physician Clinical Index (Main Interface)
Developed by: Selim Ahmed (amit.khanna.1082@gmail.com)
MIT License

THIS IS THE PRIMARY PHYSICIAN INTERFACE.
Step 1: Enter Diagnostic Data (Patient, Tumor, Depth, Size)
Step 2: Click "Auto-Calculate" -> Generates Treatment Instructions (SOP)
Step 3: Click "Run Auto-Treatment" -> Executes the plan automatically
Step 4: Click "Generate Report" -> Saves clinical documentation
"""
import sys
import os
import csv
import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QTextCursor

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from src.hardware_interface import HardwareInterface
from src.resonance_engine import ResonanceEngine, SweepWorker

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🧬 ACRS v3.0 — Physician Clinical Index")
        self.setGeometry(50, 50, 1400, 920)
        
        # Hardware & Engines
        self.hw = HardwareInterface()
        self.engine = ResonanceEngine(self.hw)
        self.sweep_worker = None
        
        # State Variables
        self.current_freq = 100000
        self.is_tracking = False
        self.log_entries = []
        self.sweep_results = None  # Stores (peak_freq, peak_amp)
        
        # Build the UI
        self.init_ui()
        self.apply_styles()
        
        # Real-time update timer (100ms)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_live_data)
        self.timer.start(100)
        
        self.log_message("🏥 System Ready. Please connect to hardware.")
        self.update_status_card("DISCONNECTED", "#ff4444")

    # ============================================================
    #  MAIN UI BUILDER (THE INDEX)
    # ============================================================
    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # --- Top Status Bar ---
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("⚪ Disconnected")
        self.status_label.setStyleSheet("font-weight: bold; padding: 5px;")
        self.status_bar.addWidget(self.status_label)
        
        # --- Tab Widget (The Index) ---
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setDocumentMode(True)
        
        # TAB 1: PHYSICIAN CLINICAL INDEX (The Main Screen)
        self.clinical_tab = QWidget()
        self.setup_clinical_index()  # <-- THIS IS THE PHYSICIAN'S INDEX
        self.tabs.addTab(self.clinical_tab, "📋 Clinical Index (Physician)")
        
        # TAB 2: Live Dashboard (Monitoring)
        self.dashboard_tab = QWidget()
        self.setup_dashboard_tab()
        self.tabs.addTab(self.dashboard_tab, "📊 Live Monitor")
        
        # TAB 3: Manual Controls (Engineering)
        self.control_tab = QWidget()
        self.setup_control_tab()
        self.tabs.addTab(self.control_tab, "⚙️ Manual Controls")
        
        # TAB 4: Graphs (Visualization)
        self.graphs_tab = QWidget()
        self.setup_graphs_tab()
        self.tabs.addTab(self.graphs_tab, "📈 Graphs")
        
        # TAB 5: Logs
        self.logs_tab = QWidget()
        self.setup_logs_tab()
        self.tabs.addTab(self.logs_tab, "📜 System Logs")
        
        main_layout.addWidget(self.tabs)
        
        # --- Bottom Footer ---
        footer = QHBoxLayout()
        footer.addWidget(QLabel("🧬 ACRS v3.0 | MIT License | Developed by Selim Ahmed"))
        footer.addStretch()
        self.freq_display_bottom = QLabel("Freq: 0 Hz")
        self.freq_display_bottom.setStyleSheet("font-weight: bold; color: #0a1128;")
        footer.addWidget(self.freq_display_bottom)
        main_layout.addLayout(footer)

    # ============================================================
    #  TAB 1: THE PHYSICIAN CLINICAL INDEX (CORE)
    # ============================================================
    def setup_clinical_index(self):
        """This is the primary screen for the doctor."""
        layout = QVBoxLayout(self.clinical_tab)
        layout.setSpacing(20)
        
        # --- SECTION 1: HARDWARE CONNECTION (Quick Access) ---
        conn_group = QGroupBox("🔗 Step 0: Hardware Connection")
        conn_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        conn_layout = QHBoxLayout()
        
        self.port_combo = QComboBox()
        self.port_combo.addItems(self.hw.scan_ports())
        self.port_combo.setMinimumWidth(150)
        self.refresh_ports_btn = QPushButton("🔄 Refresh")
        self.refresh_ports_btn.clicked.connect(self.refresh_ports)
        self.connect_btn = QPushButton("🔗 Connect")
        self.connect_btn.clicked.connect(self.toggle_connection)
        self.connect_btn.setStyleSheet("background-color: #1976d2; color: white; font-weight: bold; padding: 8px 20px;")
        self.status_indicator = QLabel("⚪ OFFLINE")
        self.status_indicator.setStyleSheet("font-weight: bold; color: #d32f2f; font-size: 14px;")
        
        conn_layout.addWidget(QLabel("Port:"))
        conn_layout.addWidget(self.port_combo)
        conn_layout.addWidget(self.refresh_ports_btn)
        conn_layout.addWidget(self.connect_btn)
        conn_layout.addWidget(QLabel("Status:"))
        conn_layout.addWidget(self.status_indicator)
        conn_layout.addStretch()
        conn_group.setLayout(conn_layout)
        layout.addWidget(conn_group)
        
        # --- SECTION 2: PATIENT DIAGNOSTIC DATA INPUT ---
        diag_group = QGroupBox("📋 Step 1: Enter Patient Diagnostic Data")
        diag_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        diag_layout = QGridLayout()
        diag_layout.setVerticalSpacing(15)
        
        # Row 0
        diag_layout.addWidget(QLabel("Patient Name:"), 0, 0)
        self.patient_name = QLineEdit("John Doe")
        self.patient_name.setStyleSheet("padding: 6px;")
        diag_layout.addWidget(self.patient_name, 0, 1)
        
        diag_layout.addWidget(QLabel("Patient ID:"), 0, 2)
        self.patient_id = QLineEdit("P-2026-001")
        self.patient_id.setStyleSheet("padding: 6px;")
        diag_layout.addWidget(self.patient_id, 0, 3)
        
        # Row 1
        diag_layout.addWidget(QLabel("Tumor Type:"), 1, 0)
        self.tumor_type = QComboBox()
        self.tumor_type.addItems(["Liver", "Pancreas", "Breast", "Brain (GBM)", "Lung", "Skin/Melanoma", "Colorectal"])
        self.tumor_type.setStyleSheet("padding: 6px;")
        diag_layout.addWidget(self.tumor_type, 1, 1)
        
        diag_layout.addWidget(QLabel("Tumor Depth (cm):"), 1, 2)
        self.tumor_depth = QLineEdit("3.5")
        self.tumor_depth.setStyleSheet("padding: 6px;")
        diag_layout.addWidget(self.tumor_depth, 1, 3)
        
        diag_layout.addWidget(QLabel("Tumor Size (mm):"), 1, 4)
        self.tumor_size = QLineEdit("25")
        self.tumor_size.setStyleSheet("padding: 6px;")
        diag_layout.addWidget(self.tumor_size, 1, 5)
        
        diag_group.setLayout(diag_layout)
        layout.addWidget(diag_group)
        
        # --- SECTION 3: AUTO-CALCULATION & GENERATED INSTRUCTIONS ---
        calc_group = QGroupBox("🧮 Step 2: Auto-Calculate & Generate Treatment Instructions (SOP)")
        calc_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        calc_layout = QVBoxLayout()
        
        # Auto-Calc Button
        btn_row = QHBoxLayout()
        self.auto_calc_btn = QPushButton("⚡ Generate Instructions from Diagnostic Data")
        self.auto_calc_btn.clicked.connect(self.auto_calculate_plan)
        self.auto_calc_btn.setStyleSheet("background-color: #0a1128; color: #00d4ff; font-weight: bold; font-size: 14px; padding: 12px; border-radius: 6px;")
        btn_row.addWidget(self.auto_calc_btn)
        btn_row.addStretch()
        calc_layout.addLayout(btn_row)
        
        # Display Calculated Parameters
        params_row = QHBoxLayout()
        self.calc_start_label = QLabel("📈 Start: -- kHz")
        self.calc_start_label.setStyleSheet("font-weight: bold; color: #2e7d32; font-size: 14px; padding: 4px 12px; background: #e8f5e9; border-radius: 4px;")
        self.calc_end_label = QLabel("📉 End: -- kHz")
        self.calc_end_label.setStyleSheet("font-weight: bold; color: #c62828; font-size: 14px; padding: 4px 12px; background: #ffebee; border-radius: 4px;")
        self.calc_step_label = QLabel("📐 Step: -- kHz")
        self.calc_step_label.setStyleSheet("font-weight: bold; color: #0a1128; font-size: 14px; padding: 4px 12px; background: #e3f2fd; border-radius: 4px;")
        params_row.addWidget(self.calc_start_label)
        params_row.addWidget(self.calc_end_label)
        params_row.addWidget(self.calc_step_label)
        params_row.addStretch()
        calc_layout.addLayout(params_row)
        
        # The Instructions Box (SOP)
        calc_layout.addWidget(QLabel("📄 Generated Clinical Instructions (Standard Operating Procedure):"))
        self.sop_text = QTextEdit()
        self.sop_text.setReadOnly(True)
        self.sop_text.setPlaceholderText("Enter patient data and click 'Generate Instructions'...")
        self.sop_text.setFont(QFont("Consolas", 11))
        self.sop_text.setMinimumHeight(180)
        self.sop_text.setStyleSheet("background-color: #f8faff; border: 1px solid #b0c4de; border-radius: 4px; padding: 8px;")
        calc_layout.addWidget(self.sop_text)
        
        calc_group.setLayout(calc_layout)
        layout.addWidget(calc_group)
        
        # --- SECTION 4: EXECUTION & REPORTING (THE ACTION) ---
        action_group = QGroupBox("🚀 Step 3: Execute Plan & Generate Report")
        action_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        action_layout = QHBoxLayout()
        
        self.run_auto_btn = QPushButton("▶ Run Full Automated Treatment")
        self.run_auto_btn.clicked.connect(self.run_auto_treatment)
        self.run_auto_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; font-size: 16px; padding: 15px 30px; border-radius: 8px;")
        
        self.generate_report_btn = QPushButton("📄 Generate Patient Report")
        self.generate_report_btn.clicked.connect(self.generate_patient_report)
        self.generate_report_btn.setStyleSheet("background-color: #ff9800; color: white; font-weight: bold; font-size: 14px; padding: 15px 25px; border-radius: 8px;")
        
        self.emergency_btn = QPushButton("🛑 EMERGENCY STOP")
        self.emergency_btn.clicked.connect(self.emergency_stop)
        self.emergency_btn.setStyleSheet("background-color: #d32f2f; color: white; font-weight: bold; font-size: 16px; padding: 15px 30px; border-radius: 8px;")
        
        self.clear_btn = QPushButton("🗑️ Clear Form")
        self.clear_btn.clicked.connect(self.clear_plan)
        self.clear_btn.setStyleSheet("padding: 15px 20px; border-radius: 8px;")
        
        action_layout.addWidget(self.run_auto_btn)
        action_layout.addWidget(self.generate_report_btn)
        action_layout.addWidget(self.emergency_btn)
        action_layout.addWidget(self.clear_btn)
        action_group.setLayout(action_layout)
        layout.addWidget(action_group)
        
        # Progress bar for sweep
        self.sweep_progress = QProgressBar()
        self.sweep_progress.setValue(0)
        self.sweep_progress.setStyleSheet("QProgressBar::chunk { background-color: #1976d2; }")
        layout.addWidget(self.sweep_progress)

    # ============================================================
    #  CLINICAL LOGIC (Auto-Calculate, SOP, Auto-Treatment, Report)
    # ============================================================
    def auto_calculate_plan(self):
        """Physician presses this -> gets instant clinical instructions."""
        try:
            depth = float(self.tumor_depth.text())
            tumor = self.tumor_type.currentText()
        except:
            QMessageBox.critical(self, "Input Error", "Please enter a valid numeric depth (e.g., 3.5).")
            return

        # --- Smart Algorithm (Clinical Rules) ---
        if "Brain" in tumor:
            start_khz, end_khz = 150, 500
        elif "Liver" in tumor or "Pancreas" in tumor:
            start_khz, end_khz = 80, 300
        elif "Breast" in tumor or "Skin" in tumor:
            start_khz, end_khz = 500, 1500
        else:  # Lung, Colorectal
            start_khz, end_khz = 100, 400
            
        # Adjust for depth (clinical rule: deeper tissue = lower freq for penetration)
        if depth > 5.0:
            start_khz = max(50, start_khz - 50)
            end_khz = max(200, end_khz - 100)
        elif depth < 2.0:
            start_khz = min(800, start_khz + 200)
            end_khz = min(3000, end_khz + 500)
            
        step_khz = max(5, int((end_khz - start_khz) / 30))

        # Update UI
        self.calc_start_label.setText(f"📈 Start: {start_khz:.1f} kHz")
        self.calc_end_label.setText(f"📉 End: {end_khz:.1f} kHz")
        self.calc_step_label.setText(f"📐 Step: {step_khz:.1f} kHz")
        
        self._plan_start = int(start_khz * 1000)
        self._plan_end = int(end_khz * 1000)
        self._plan_step = int(step_khz * 1000)

        # --- Generate the Clinical Instructions (SOP) ---
        sop = f"""
================================================================================
                    STANDARD OPERATING PROCEDURE (SOP)
                          CLINICAL TREATMENT PLAN
================================================================================

PATIENT: {self.patient_name.text()} (ID: {self.patient_id.text()})
TUMOR: {tumor} | DEPTH: {depth} cm | SIZE: {self.tumor_size.text()} mm

--------------------------------------------------------------------------------
1.  CALCULATED TREATMENT PARAMETERS
--------------------------------------------------------------------------------
    • Frequency Sweep Range  : {start_khz:.1f} kHz  →  {end_khz:.1f} kHz
    • Sweep Step Size        : {step_khz:.1f} kHz
    • Total Sweep Steps      : {int((end_khz - start_khz) / step_khz)}
    • Expected Sweep Duration: ~{int((end_khz - start_khz) / step_khz) * 2} seconds

--------------------------------------------------------------------------------
2.  PHYSICIAN INSTRUCTIONS (PRE-TREATMENT)
--------------------------------------------------------------------------------
    a) Verify hardware is connected (Port: {self.port_combo.currentText()}).
    b) Click the "Run Full Automated Treatment" button below.
    c) The system will:
       - Connect to the hardware (if not already).
       - Set the starting frequency.
       - Automatically sweep the range to find the RESONANCE PEAK.
       - Lock the system onto the optimal frequency.
       - Enable Auto-Track (PLL) to maintain resonance during the session.
    d) Monitor the "Live Monitor" tab for Frequency, Phase, and Amplitude.

--------------------------------------------------------------------------------
3.  EMERGENCY & SAFETY
--------------------------------------------------------------------------------
    • If any abnormality is observed, press the "EMERGENCY STOP" button immediately.
    • The system will cut all output power to the patient applicator.

--------------------------------------------------------------------------------
4.  POST-TREATMENT
--------------------------------------------------------------------------------
    • Click "Generate Patient Report" to save a timestamped clinical record.
    • Attach this report to the patient's medical file.

================================================================================
                    END OF CLINICAL INSTRUCTIONS
================================================================================
"""
        self.sop_text.setText(sop)
        self.log_message(f"✅ Clinical instructions generated for {self.patient_name.text()}")

    def run_auto_treatment(self):
        """One-click full automation for the physician."""
        if not self.hw.is_connected:
            reply = QMessageBox.question(self, "Hardware Offline", 
                                         "Hardware is not connected. Connect now?", 
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.toggle_connection()
                if not self.hw.is_connected:
                    return
            else:
                return
        
        if not hasattr(self, '_plan_start') or self._plan_start is None:
            QMessageBox.information(self, "Missing Plan", "Please click 'Generate Instructions' first.")
            return
            
        self.log_message("🚀 Initiating Full Auto-Treatment Sequence...")
        self.run_auto_btn.setEnabled(False)
        self.auto_calc_btn.setEnabled(False)

        # Disable manual tracking
        self.is_tracking = False
        self.track_check.setChecked(False)

        # Step 1: Set starting frequency
        self.hw.set_frequency(self._plan_start)
        
        # Step 2: Start Sweep
        self.sweep_worker = SweepWorker(self.hw, self._plan_start, self._plan_end, self._plan_step)
        self.sweep_worker.progress.connect(self.on_sweep_progress)
        self.sweep_worker.finished.connect(self.on_auto_sweep_finished)
        self.sweep_worker.log.connect(self.log_message)
        self.sweep_worker.start()
        self.log_message("🔍 Sweeping for resonance peak...")

    def on_auto_sweep_finished(self, peak_freq, peak_amp, freq_data, amp_data, phase_data):
        self.engine.set_sweep_data(freq_data, amp_data, phase_data)
        self.sweep_results = (peak_freq, peak_amp)
        
        self.current_freq = peak_freq
        self.hw.set_frequency(self.current_freq)
        
        self.log_message(f"✅ Resonance locked at {peak_freq/1000:.2f} kHz (Amplitude: {peak_amp:.2f} mV)")
        
        # Step 3: Enable PLL
        self.is_tracking = True
        self.track_check.setChecked(True)
        self.log_message("🔒 Auto-Track (PLL) ENABLED. System is now maintaining resonance.")
        
        # Re-enable UI
        self.run_auto_btn.setEnabled(True)
        self.auto_calc_btn.setEnabled(True)
        self.sweep_progress.setValue(100)
        
        self.update_graphs()
        self.tabs.setCurrentIndex(3)  # Switch to Graphs
        
        QMessageBox.information(self, "✅ Treatment Complete", 
                                f"Resonance locked at {peak_freq/1000:.2f} kHz.\n"
                                f"PLL is active. Monitor the Live Monitor tab.")

    def generate_patient_report(self):
        """Saves a clinical report for the physician's records."""
        if not self.sweep_results:
            QMessageBox.warning(self, "No Data", "Run a treatment first to generate a report.")
            return
            
        peak_freq, peak_amp = self.sweep_results
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""
================================================================================
                    ANTI-CANCER RESONANCE TREATMENT
                         CLINICAL PATIENT REPORT
================================================================================
Generated: {now}
Software: ACRS v3.0 (MIT License)
Developer: Selim Ahmed

--------------------------------------------------------------------------------
1.  PATIENT INFORMATION
--------------------------------------------------------------------------------
    Name            : {self.patient_name.text()}
    ID              : {self.patient_id.text()}
    Tumor Type      : {self.tumor_type.currentText()}
    Tumor Depth     : {self.tumor_depth.text()} cm
    Tumor Size      : {self.tumor_size.text()} mm

--------------------------------------------------------------------------------
2.  TREATMENT PARAMETERS & RESULTS
--------------------------------------------------------------------------------
    Sweep Range     : {self.calc_start_label.text()}  →  {self.calc_end_label.text()}
    Step Size       : {self.calc_step_label.text()}
    Resonant Freq   : {peak_freq/1000:.2f} kHz
    Peak Amplitude  : {peak_amp:.2f} mV
    Auto-Track (PLL): {'✅ ENABLED' if self.is_tracking else '❌ DISABLED'}

--------------------------------------------------------------------------------
3.  CLINICAL INSTRUCTIONS (SOP)
--------------------------------------------------------------------------------
{self.sop_text.toPlainText()}

--------------------------------------------------------------------------------
4.  SYSTEM STATUS
--------------------------------------------------------------------------------
    Hardware Status : {'✅ Connected' if self.hw.is_connected else '❌ Disconnected'}
    Output Freq     : {self.current_freq/1000:.2f} kHz

================================================================================
                    END OF REPORT
================================================================================
"""
        os.makedirs("logs", exist_ok=True)
        filename = f"logs/Clinical_Report_{self.patient_id.text()}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w') as f:
            f.write(report)
        
        self.log_message(f"📄 Clinical report saved to {filename}")
        QMessageBox.information(self, "Report Saved", f"Clinical report saved to:\n{filename}")

    def clear_plan(self):
        """Resets the form for the next patient."""
        self.sop_text.clear()
        self.calc_start_label.setText("📈 Start: -- kHz")
        self.calc_end_label.setText("📉 End: -- kHz")
        self.calc_step_label.setText("📐 Step: -- kHz")
        self.patient_name.setText("")
        self.patient_id.setText("")
        self.tumor_depth.setText("")
        self.tumor_size.setText("")
        self.sweep_progress.setValue(0)
        if hasattr(self, '_plan_start'): del self._plan_start
        self.sweep_results = None
        self.log_message("🗑️ Form cleared. Ready for next patient.")

    # ============================================================
    #  LIVE DASHBOARD TAB (MONITORING)
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
        layout.addStretch()

    def create_card(self, title, value, object_name):
        card = QGroupBox(title)
        card.setStyleSheet("""QGroupBox { font-weight: bold; font-size: 14px; border: 1px solid #ccc; border-radius: 8px; margin-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }""")
        layout = QVBoxLayout()
        label = QLabel(value)
        label.setObjectName(object_name)
        label.setAlignment(Qt.AlignCenter)
        label.setFont(QFont("Arial", 24, QFont.Bold))
        label.setStyleSheet("color: #1976d2; padding: 15px;")
        layout.addWidget(label)
        card.setLayout(layout)
        return card

    # ============================================================
    #  MANUAL CONTROLS TAB (FOR ENGINEERS)
    # ============================================================
    def setup_control_tab(self):
        layout = QVBoxLayout(self.control_tab)
        grid = QGridLayout()
        grid.addWidget(QLabel("Start (kHz):"), 0, 0)
        self.sweep_min_input = QLineEdit("100")
        grid.addWidget(self.sweep_min_input, 0, 1)
        grid.addWidget(QLabel("End (kHz):"), 0, 2)
        self.sweep_max_input = QLineEdit("5000")
        grid.addWidget(self.sweep_max_input, 0, 3)
        grid.addWidget(QLabel("Step (kHz):"), 0, 4)
        self.sweep_step_input = QLineEdit("50")
        grid.addWidget(self.sweep_step_input, 0, 5)
        
        self.sweep_btn = QPushButton("▶ Start Sweep")
        self.sweep_btn.clicked.connect(self.start_sweep)
        self.stop_sweep_btn = QPushButton("⏹ Stop")
        self.stop_sweep_btn.clicked.connect(self.stop_sweep)
        self.stop_sweep_btn.setEnabled(False)
        grid.addWidget(self.sweep_btn, 1, 0, 1, 3)
        grid.addWidget(self.stop_sweep_btn, 1, 3, 1, 3)
        
        grid.addWidget(QLabel("Manual (Hz):"), 2, 0)
        self.manual_freq_input = QLineEdit("100000")
        grid.addWidget(self.manual_freq_input, 2, 1)
        self.set_freq_btn = QPushButton("Set")
        self.set_freq_btn.clicked.connect(self.manual_set_freq)
        grid.addWidget(self.set_freq_btn, 2, 2)
        
        self.track_check = QCheckBox("Enable Auto-Track (PLL)")
        self.track_check.stateChanged.connect(self.toggle_tracking)
        grid.addWidget(self.track_check, 3, 0, 1, 3)
        layout.addLayout(grid)
        layout.addStretch()

    # ============================================================
    #  GRAPHS TAB
    # ============================================================
    def setup_graphs_tab(self):
        layout = QVBoxLayout(self.graphs_tab)
        self.figure = Figure(figsize=(10, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.ax1 = self.figure.add_subplot(211)
        self.ax2 = self.figure.add_subplot(212)
        self.ax1.set_title("Amplitude vs Frequency")
        self.ax1.set_xlabel("Frequency (kHz)")
        self.ax1.set_ylabel("Amplitude (mV)")
        self.ax1.grid(True, alpha=0.3)
        self.ax2.set_title("Phase vs Frequency")
        self.ax2.set_xlabel("Frequency (kHz)")
        self.ax2.set_ylabel("Phase (°)")
        self.ax2.grid(True, alpha=0.3)
        self.ax2.axhline(y=0, color='r', linestyle='--', alpha=0.5)
        layout.addWidget(self.canvas)

    # ============================================================
    #  LOGS TAB
    # ============================================================
    def setup_logs_tab(self):
        layout = QVBoxLayout(self.logs_tab)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 10))
        layout.addWidget(self.log_text)
        btn_layout = QHBoxLayout()
        self.export_btn = QPushButton("💾 Export CSV")
        self.export_btn.clicked.connect(self.export_logs)
        self.clear_logs_btn = QPushButton("🗑️ Clear")
        self.clear_logs_btn.clicked.connect(lambda: self.log_text.clear())
        btn_layout.addWidget(self.export_btn)
        btn_layout.addWidget(self.clear_logs_btn)
        layout.addLayout(btn_layout)

    # ============================================================
    #  CORE HARDWARE & SHARED FUNCTIONS
    # ============================================================
    def refresh_ports(self):
        ports = self.hw.scan_ports()
        self.port_combo.clear()
        self.port_combo.addItems(ports)

    def toggle_connection(self):
        if self.hw.is_connected:
            self.hw.disconnect()
            self.connect_btn.setText("🔗 Connect")
            self.status_label.setText("⚪ Disconnected")
            self.status_indicator.setText("⚪ OFFLINE")
            self.status_indicator.setStyleSheet("font-weight: bold; color: #d32f2f;")
            self.update_status_card("OFFLINE", "#ff4444")
            self.log_message("Disconnected.")
        else:
            port = self.port_combo.currentText()
            success, msg = self.hw.connect(port)
            if success:
                self.connect_btn.setText("🔌 Disconnect")
                self.status_label.setText(f"🟢 Connected to {port}")
                self.status_indicator.setText("🟢 ONLINE")
                self.status_indicator.setStyleSheet("font-weight: bold; color: #4CAF50;")
                self.update_status_card("ONLINE", "#4CAF50")
                self.current_freq = self.hw.get_frequency() or 100000
                self.log_message(f"Connected to {port}")
            else:
                QMessageBox.critical(self, "Error", msg)

    def update_status_card(self, text, color):
        label = self.dashboard_tab.findChild(QLabel, "status_val")
        if label:
            label.setText(text)
            label.setStyleSheet(f"color: {color}; padding: 15px; font-weight: bold;")

    def update_live_data(self):
        if not self.hw.is_connected:
            return
        freq = self.hw.get_frequency()
        if freq and freq > 0: self.current_freq = freq
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
        if self.engine.freq_data:
            self.update_graphs()

    def update_graphs(self):
        self.ax1.clear(); self.ax2.clear()
        if self.engine.freq_data:
            freqs_khz = [f/1000 for f in self.engine.freq_data]
            self.ax1.plot(freqs_khz, self.engine.amp_data, 'b-', linewidth=2)
            self.ax1.grid(True, alpha=0.3)
            if self.engine.phase_data:
                self.ax2.plot(freqs_khz, self.engine.phase_data, 'r-', linewidth=2)
                self.ax2.axhline(y=0, color='k', linestyle='--', alpha=0.5)
                self.ax2.grid(True, alpha=0.3)
        self.canvas.draw()

    def start_sweep(self):
        if not self.hw.is_connected: return
        start_freq = int(float(self.sweep_min_input.text()) * 1000)
        end_freq = int(float(self.sweep_max_input.text()) * 1000)
        step = int(float(self.sweep_step_input.text()) * 1000)
        self.sweep_btn.setEnabled(False); self.stop_sweep_btn.setEnabled(True)
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

    def manual_set_freq(self):
        if not self.hw.is_connected: return
        try:
            freq = int(self.manual_freq_input.text())
            self.hw.set_frequency(freq); self.current_freq = freq
        except: pass

    def toggle_tracking(self, state):
        self.is_tracking = (state == Qt.Checked)

    def emergency_stop(self):
        self.is_tracking = False
        self.track_check.setChecked(False)
        if self.hw.is_connected: self.hw.set_frequency(0)
        self.log_message("🛑 EMERGENCY STOP ACTIVATED.")
        QMessageBox.warning(self, "Emergency Stop", "Output has been disabled.")

    def export_logs(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Logs", "logs/session.csv", "CSV (*.csv)")
        if path:
            with open(path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Message"])
                for entry in self.log_entries: writer.writerow([entry])

    def log_message(self, msg):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {msg}"
        self.log_entries.append(formatted)
        self.log_text.append(formatted)
        self.log_text.moveCursor(QTextCursor.End)

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #f5f9fc; }
            QTabWidget::pane { border: 1px solid #b0c4de; background: white; border-radius: 8px; }
            QTabBar::tab { background: #dde8f0; padding: 10px 20px; margin-right: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px; font-weight: 600; }
            QTabBar::tab:selected { background: #0a1128; color: #00d4ff; }
            QGroupBox { font-weight: bold; border: 1px solid #b0c4de; border-radius: 8px; margin-top: 12px; background: white; }
            QGroupBox::title { subcontrol-origin: margin; left: 15px; padding: 0 10px; }
            QPushButton { border-radius: 6px; padding: 8px 16px; font-weight: 600; }
            QLineEdit, QComboBox { padding: 8px; border: 1px solid #b0c4de; border-radius: 4px; background: white; }
            QProgressBar { height: 24px; border-radius: 6px; border: 1px solid #b0c4de; }
            QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1976d2, stop:1 #00d4ff); border-radius: 6px; }
            QTextEdit { border: 1px solid #b0c4de; border-radius: 4px; background: #fafcff; }
        """)

    def closeEvent(self, event):
        self.timer.stop()
        if self.sweep_worker and self.sweep_worker.isRunning():
            self.sweep_worker.stop(); self.sweep_worker.wait()
        self.hw.disconnect()
        event.accept()
