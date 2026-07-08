"""
Resonance Engine - Sweep and PLL algorithms for real hardware.
Developed by: Selim Ahmed (amit.khanna.1082@gmail.com)
"""
import time
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal

class SweepWorker(QThread):
    """Threaded sweep to prevent GUI freezing."""
    progress = pyqtSignal(int, int, float, float)  # current_freq, total, amp, phase
    finished = pyqtSignal(int, float)  # resonant_freq, peak_amp
    log = pyqtSignal(str)
    
    def __init__(self, hw, start_freq, end_freq, step):
        super().__init__()
        self.hw = hw
        self.start = start_freq
        self.end = end_freq
        self.step = step
        self._is_running = True

    def stop(self):
        self._is_running = False

    def run(self):
        self.log.emit(f"Starting sweep from {self.start/1000:.1f}kHz to {self.end/1000:.1f}kHz")
        freq_data = []
        amp_data = []
        
        f = self.start
        peak_freq = self.start
        peak_amp = 0
        
        total_steps = int((self.end - self.start) / self.step) + 1
        
        while f <= self.end and self._is_running:
            success = self.hw.set_frequency(f)
            if not success:
                self.log.emit("Error setting frequency. Check hardware.")
                break
            
            time.sleep(0.02)  # Settling time
            amp = self.hw.read_amplitude()
            phase = self.hw.read_phase()
            
            freq_data.append(f)
            amp_data.append(amp)
            
            if amp > peak_amp:
                peak_amp = amp
                peak_freq = f
                
            current_step = int((f - self.start) / self.step) + 1
            self.progress.emit(current_step, total_steps, f, phase)
            self.log.emit(f"Sweep: {f/1000:.1f}kHz | Amp: {amp:.3f}mV | Phase: {phase:.1f}°")
            
            f += self.step
        
        if self._is_running:
            self.finished.emit(peak_freq, peak_amp)
            self.log.emit(f"Sweep complete. Resonance at {peak_freq/1000:.1f}kHz")
        else:
            self.log.emit("Sweep stopped by user.")

class ResonanceEngine:
    def __init__(self, hw_interface):
        self.hw = hw_interface
        self.resonant_freq = None
        self.freq_data = []
        self.amp_data = []
        self.phase_data = []

    def pll_update(self, current_freq, phase, kp=0.08):
        """
        Simple Phase-Locked Loop update based on real phase reading.
        Phase = 0 is target.
        """
        error = -phase  # Invert because we want to null the error
        delta = kp * error
        new_freq = current_freq + delta
        # Clamp to a safe range (1kHz - 20MHz)
        new_freq = max(1000, min(20000000, new_freq))
        return int(new_freq)
