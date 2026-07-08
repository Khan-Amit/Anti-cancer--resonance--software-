# Anti-cancer--resonance--software-
Medical software 
# Anti-Cancer Resonance Software (ACRS)

**Developed by:** seliim Ahmed (amit.khanna.1082@gmail.com)  
**License:** MIT (Free for everyone, anywhere)  
**Status:** Simulation & Algorithm Prototype

## 🧬 Overview
This software is designed to control and automate resonance-based medical devices (such as Cytotron or TTFields systems). It provides a real-time graphical interface to:
- Sweep frequencies to find the biological resonant peak.
- Auto-track the resonance using a Phase-Locked Loop (PLL).
- Log all treatment data (frequency, amplitude, phase) to CSV.

## ✨ Key Features
- **Interactive GUI**: Real-time amplitude/frequency plotting.
- **Automatic Sweep**: Finds the optimal resonant frequency.
- **PLL Auto-Tracking**: Dynamically adjusts frequency to maintain resonance as the load changes.
- **Simulation Mode**: Run completely without hardware to test algorithms.
- **Data Logging**: Saves all parameters for clinical documentation.

## 🛠️ Installation
1. Clone this repository:
   ```bash
   git clone https://github.com/Khan-Amit/Anti-cancer--resonance--software-.git
   cd Anti-cancer--resonance--software-

   python main.py




   python main.py


   Anti-cancer--resonance--software/
├── README.md (Updated)
├── LICENSE (MIT)
├── requirements.txt
├── main.py
├── src/
│   ├── hardware_interface.py  (NO simulation, pure Serial)
│   └── resonance_engine.py    (Sweep + PLL using real hardware)
├── gui/
│   ├── main_window.py         (New Tabbed Dashboard UI)
│   └── styles.py              (Modern dark/light styling)
└── logs/
