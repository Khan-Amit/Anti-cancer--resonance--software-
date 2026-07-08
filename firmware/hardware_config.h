/**
 * hardware_config.h - Pin mapping and constants
 * Adjust these for your specific microcontroller and hardware.
 */

#ifndef HARDWARE_CONFIG_H
#define HARDWARE_CONFIG_H

// ------------------------------------------------------------------
// Serial Communication
// ------------------------------------------------------------------
#define SERIAL_BAUD 115200

// ------------------------------------------------------------------
// DDS AD9850 / AD9851 Pins
// ------------------------------------------------------------------
#define DDS_CLK_PIN   13   // Clock (SCLK) - connects to AD9850 CLK
#define DDS_DATA_PIN  11   // Data (SDATA) - connects to AD9850 DATA
#define DDS_FQ_UD_PIN 10   // Frequency Update (FQ_UD) - connects to AD9850 FQ_UD
#define DDS_RESET_PIN 9    // Reset - connects to AD9850 RESET

// ------------------------------------------------------------------
// ADC Pins for Phase and Amplitude
// ------------------------------------------------------------------
// ESP32: Use ADC1 pins (GPIO 32-39)
// Arduino Uno: Use A0, A1
// STM32: Use PA0, PA1
#ifdef ESP32
    #define PHASE_ADC_PIN  34   // AD8302 phase output
    #define AMP_ADC_PIN    35   // Peak detector / amplitude output
#elif defined(ARDUINO_AVR_UNO) || defined(ARDUINO_AVR_MEGA)
    #define PHASE_ADC_PIN  A0
    #define AMP_ADC_PIN    A1
#else
    // Default for generic Arduino/STM32
    #define PHASE_ADC_PIN  A0
    #define AMP_ADC_PIN    A1
#endif

// ------------------------------------------------------------------
// ADC Settings
// ------------------------------------------------------------------
#define ADC_MAX          4095.0   // ESP32 (12-bit) = 4095; Arduino (10-bit) = 1023
#define ADC_REF_VOLTAGE  3.3      // ESP32 = 3.3V; Arduino 5V

// ------------------------------------------------------------------
// Frequency Limits
// ------------------------------------------------------------------
#define MIN_FREQ  1000     // 1 kHz minimum
#define MAX_FREQ  20000000 // 20 MHz maximum (AD9850 max is 40 MHz)

#endif
