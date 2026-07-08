"""
Hardware Interface - Strictly for physical Serial/RS-232 devices.
Developed by: Selim Ahmed (amit.khanna.1082@gmail.com)
"""
import serial
import serial.tools.list_ports
import time
import threading

class HardwareInterface:
    def __init__(self, port='COM3', baud=115200, timeout=1):
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self.ser = None
        self.is_connected = False
        self.lock = threading.Lock()

    def scan_ports(self):
        """Return a list of available COM ports."""
        ports = [port.device for port in serial.tools.list_ports.comports()]
        return ports

    def connect(self, port=None):
        """Establish connection to the hardware."""
        if port:
            self.port = port
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=self.timeout)
            time.sleep(0.5)  # Allow device to reset
            self.is_connected = True
            return True, f"Connected to {self.port}"
        except Exception as e:
            self.is_connected = False
            return False, f"Connection failed: {str(e)}"

    def disconnect(self):
        """Close the serial connection."""
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.is_connected = False
        return "Disconnected"

    def send_command(self, cmd, read_response=True):
        """
        Send a command to the hardware and optionally read the response.
        Hardware protocol expects:
        - SET_FREQ <Hz> -> Should return "OK" or actual set frequency.
        - READ_PHASE -> Returns a float (e.g., "-12.5").
        - READ_AMP   -> Returns a float (e.g., "2.45").
        """
        if not self.is_connected or not self.ser or not self.ser.is_open:
            raise ConnectionError("Hardware not connected.")
        
        with self.lock:
            self.ser.reset_input_buffer()
            self.ser.write(f"{cmd}\n".encode())
            time.sleep(0.01)  # Small delay for device processing
            
            if read_response:
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                return line
            return "OK"

    def set_frequency(self, freq_hz):
        """Sets the output frequency. Returns True on success."""
        try:
            resp = self.send_command(f"SET_FREQ {int(freq_hz)}")
            return "OK" in resp or "ACK" in resp or resp != ""
        except:
            return False

    def read_phase(self):
        """Returns the phase difference in degrees as a float."""
        try:
            resp = self.send_command("READ_PHASE")
            return float(resp)
        except:
            return 0.0

    def read_amplitude(self):
        """Returns the amplitude in mV as a float."""
        try:
            resp = self.send_command("READ_AMP")
            return float(resp)
        except:
            return 0.0

    def get_frequency(self):
        """Ask hardware for current frequency (optional)."""
        try:
            resp = self.send_command("READ_FREQ")
            return int(resp)
        except:
            return 0

    def is_open(self):
        return self.is_connected and self.ser and self.ser.is_open
