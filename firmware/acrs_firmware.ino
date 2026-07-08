/**
 * ACRS Firmware v1.0
 * Anti-Cancer Resonance Software - Hardware Interface
 * 
 * Developed by: Selim Ahmed (amit.khanna.1082@gmail.com)
 * License: MIT
 * 
 * Protocol:
 * - SET_FREQ <Hz>  -> Sets output frequency
 * - READ_PHASE      -> Returns phase difference in degrees (float)
 * - READ_AMP        -> Returns amplitude in mV (float)
 * - READ_FREQ       -> Returns current frequency in Hz (int)
 * 
 * Hardware:
 * - MCU: ESP32, STM32, Arduino Mega/Uno
 * - DDS: AD9850 (or AD9851) for sine wave generation
 * - Phase Detector: AD8302 (outputs voltage proportional to phase)
 * - Amplitude Detector: Simple peak detector or ADC on antenna feedback
 */

#include "hardware_config.h"
#include "dds_controller.h"
#include "serial_commands.h"

// ------------------------------------------------------------------
// Global Variables
// ------------------------------------------------------------------
DDSController dds(DDS_CLK_PIN, DDS_DATA_PIN, DDS_FQ_UD_PIN, DDS_RESET_PIN);
SerialCommands serialParser;

unsigned long last_phase_read = 0;
unsigned long last_amp_read = 0;
float current_phase = 0.0;
float current_amplitude = 0.0;
unsigned long current_freq_hz = 100000; // Default: 100 kHz

// ------------------------------------------------------------------
// Setup
// ------------------------------------------------------------------
void setup() {
    Serial.begin(SERIAL_BAUD);
    Serial.println("ACRS Firmware v1.0 Ready");
    Serial.println("Commands: SET_FREQ, READ_PHASE, READ_AMP, READ_FREQ");
    
    // Initialize DDS
    dds.init();
    dds.setFrequency(current_freq_hz);
    
    // Initialize ADC for phase/amplitude reading
    pinMode(PHASE_ADC_PIN, INPUT);
    pinMode(AMP_ADC_PIN, INPUT);
    
    // Debug: Blink LED to show alive status
    pinMode(LED_BUILTIN, OUTPUT);
    digitalWrite(LED_BUILTIN, HIGH);
}

// ------------------------------------------------------------------
// Main Loop
// ------------------------------------------------------------------
void loop() {
    // 1. Process incoming serial commands
    if (Serial.available()) {
        String cmd = Serial.readStringUntil('\n');
        cmd.trim();
        processCommand(cmd);
    }
    
    // 2. Periodically read phase and amplitude (every 50ms)
    unsigned long now = millis();
    if (now - last_phase_read > 50) {
        current_phase = readPhase();
        current_amplitude = readAmplitude();
        last_phase_read = now;
    }
    
    // 3. Blink LED to show activity
    static unsigned long last_blink = 0;
    if (now - last_blink > 1000) {
        digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
        last_blink = now;
    }
}

// ------------------------------------------------------------------
// Command Processor
// ------------------------------------------------------------------
void processCommand(String cmd) {
    cmd.toLowerCase();
    
    if (cmd.startsWith("set_freq")) {
        // Extract frequency
        int spaceIdx = cmd.indexOf(' ');
        if (spaceIdx > 0) {
            String freqStr = cmd.substring(spaceIdx + 1);
            unsigned long freq = freqStr.toInt();
            if (freq >= MIN_FREQ && freq <= MAX_FREQ) {
                current_freq_hz = freq;
                dds.setFrequency(current_freq_hz);
                Serial.println("OK");
                Serial.println("ACK");
            } else {
                Serial.println("ERROR: Frequency out of range");
            }
        } else {
            Serial.println("ERROR: Missing frequency");
        }
    }
    else if (cmd.startsWith("read_phase")) {
        Serial.println(current_phase, 2);
    }
    else if (cmd.startsWith("read_amp")) {
        Serial.println(current_amplitude, 2);
    }
    else if (cmd.startsWith("read_freq")) {
        Serial.println(current_freq_hz);
    }
    else if (cmd.startsWith("help")) {
        Serial.println("Commands:");
        Serial.println("  SET_FREQ <Hz>  - Set output frequency (1kHz - 20MHz)");
        Serial.println("  READ_PHASE     - Return phase difference in degrees");
        Serial.println("  READ_AMP       - Return amplitude in mV");
        Serial.println("  READ_FREQ      - Return current frequency in Hz");
    }
    else if (cmd.length() > 0) {
        Serial.println("ERROR: Unknown command");
    }
}

// ------------------------------------------------------------------
// Hardware Reading Functions
// ------------------------------------------------------------------

/**
 * Read phase from AD8302 phase detector.
 * AD8302 outputs voltage from 0V to 1.8V representing -90° to +90°.
 * Mapping: 0V = -90°, 0.9V = 0°, 1.8V = +90°
 */
float readPhase() {
    int adcValue = analogRead(PHASE_ADC_PIN);
    // Convert ADC (0-4095 for ESP32, 0-1023 for Arduino Uno) to voltage
    float voltage = (adcValue / (float)ADC_MAX) * ADC_REF_VOLTAGE;
    
    // Map voltage to degrees: 0V -> -90°, ADC_REF_VOLTAGE/2 -> 0°, ADC_REF_VOLTAGE -> +90°
    float phase_deg = ((voltage / ADC_REF_VOLTAGE) * 180.0) - 90.0;
    
    // Clamp to valid range
    if (phase_deg < -90.0) phase_deg = -90.0;
    if (phase_deg > 90.0) phase_deg = 90.0;
    
    return phase_deg;
}

/**
 * Read amplitude from peak detector or RF power sensor.
 * This is a simplified version using a diode-based peak detector.
 * Adjust scaling based on your specific hardware.
 */
float readAmplitude() {
    int adcValue = analogRead(AMP_ADC_PIN);
    float voltage = (adcValue / (float)ADC_MAX) * ADC_REF_VOLTAGE;
    
    // Map voltage to mV.
    // For example: 0.5V ADC input = 100mV RF amplitude.
    // Adjust this scaling factor based on your actual circuit.
    float amp_mV = voltage * 200.0;  // Example scaling
    
    // Clamp
    if (amp_mV < 0) amp_mV = 0;
    if (amp_mV > 10000) amp_mV = 10000;  // Max 10V
    
    return amp_mV;
}
