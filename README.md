# 🧬 Anti-Cancer Resonance Software (ACRS) v3.0

**Developed by:** Selim Ahmed (amit.khanna.1082@gmail.com)  
**License:** MIT (Free for anyone to use, modify, and distribute)  
**Repository:** [github.com/Khan-Ar/Anti-cancer--resonance--software](https://github.com/Khan-Ar/Anti-cancer--resonance--software)

---

## 📖 Table of Contents (Master Index)

1. [What is ACRS?](#-what-is-acrs)
2. [The Front End Index: Treatment Planner](#-the-front-end-index-treatment-planner)
   - [Patient & Tumor Input](#1-patient--tumor-input)
   - [Auto-Calculation & SOP Generation](#2-auto-calculation--sop-generation)
   - [One-Click Auto-Treatment](#3-one-click-auto-treatment)
   - [Generate Patient Report](#4-generate-patient-report)
3. [Quick Start Guide](#-quick-start-guide)
4. [Step-by-Step Operation Guide](#-step-by-step-operation-guide)
5. [Hardware Setup](#-hardware-setup)
6. [Hardware Communication Protocol](#-hardware-communication-protocol)
7. [Compatible Devices (China & India)](#-compatible-devices-china--india)
8. [Troubleshooting](#-troubleshooting)
9. [Credits & License](#-credits--license)

---

## 🧬 What is ACRS?

**ACRS** is an open-source software platform designed to control **resonance-based cancer treatment devices** (like the Cytotron or TTFields systems). 

It provides a **medical-grade user interface** that allows operators to:
- Enter patient data.
- **Automatically calculate** the optimal frequency sweep range based on tumor type and depth.
- **Automatically generate** a Standard Operating Procedure (SOP) for the operator.
- **Run a fully automated treatment sequence** (Connect → Sweep → Find Resonance → Lock PLL).
- **Generate detailed patient reports** for clinical documentation.

> ⚠️ **Important Disclaimer**: This is a research/development tool. Do not use on humans without proper regulatory approval (FDA, CE, NMPA, CDSCO).

---

## 📋 The Front End Index: Treatment Planner

When you run the software (`python main.py`), the **"Treatment Planner"** tab is your main dashboard (Index). It is designed so that **any operator can follow it without technical knowledge**.

### 1. Patient & Tumor Input
Fill in the patient details:
- **Patient Name & ID**
- **Tumor Type** (Dropdown: Liver, Pancreas, Breast, Brain, Lung, Skin)
- **Depth (cm)** and **Size (mm)**

> This data is used by the Auto-Calculation engine.

### 2. Auto-Calculation & SOP Generation
Click the **"🧮 Auto-Calculate Frequencies & Instructions"** button.

**What happens automatically:**
- The software reads the tumor type and depth.
- It **calculates the optimal frequency range** using this logic:
  - **Brain/GBM:** 150 – 500 kHz
  - **Liver/Pancreas:** 80 – 300 kHz
  - **Breast/Skin:** 500 – 1500 kHz
  - **Deep tissues (>5 cm):** Frequencies are lowered for better penetration.
  - **Shallow tissues (<2 cm):** Frequencies are increased for better focus.
- It calculates the **optimal step size** to sweep efficiently.
- It **generates a complete Standard Operating Procedure (SOP)** in the text box below, which includes:
  - Patient name, tumor, and parameters.
  - Exact frequency settings.
  - Step-by-step instructions for the operator to follow.

### 3. One-Click Auto-Treatment
Click the **"▶ Run Full Auto-Treatment"** button.

This executes the **entire treatment sequence automatically**:
1. **Checks connection** (prompts to connect if not).
2. **Sets the starting frequency**.
3. **Performs a full frequency sweep** (using the calculated range).
4. **Detects the resonance peak** (highest amplitude).
5. **Locks the system** onto that exact frequency.
6. **Enables Auto-Track (PLL)** to continuously maintain resonance in real-time.

> After this, you can switch to the **Dashboard** tab to monitor live Frequency, Phase, and Amplitude.

### 4. Generate Patient Report
Click the **"📄 Generate Patient Report"** button.

- Saves a complete clinical report (`.txt`) to the `/logs` folder.
- The report includes:
  - Patient demographics.
  - Tumor parameters.
  - Calculated sweep settings.
  - **Detected resonant frequency and peak amplitude.**
  - The **full SOP** generated earlier.
  - System status and timestamps.

> This report can be printed or attached to medical records.

---

## 🚀 Quick Start Guide

### 1. Install Prerequisites
```bash
pip install -r requirements.txt
