# FSR Sensor Calibration for Humanoid Robot Handshake 🤖🤝

An interactive Python data acquisition and mathematical calibration tool designed to calibrate Force Sensitive Resistors (FSR) used in tendon-driven humanoid robotics. 

This repository allows researchers and engineers to map raw analog ADC values from a microcontroller (Arduino Nano / ESP32) to physical force values ($N$) measured via a dynamometer. It computes high-precision **cubic and quartic polynomial regression equations** ready for direct implementation into embedded firmware.

---

## 📌 Project Overview & Features

* **Real-time Serial Data Acquisition:** Connects directly to the microcontroller over serial (`COM` / `TTY`) to stream multi-sensor data.
* **Signal Filtering:** Samples and averages ADC readings during a configurable window ($2.0\text{ s}$) to filter mechanical noise from tendon tension adjustments.
* **Polynomial Curve Fitting:** Computes 3rd-degree (cubic) and 4th-degree (quartic) polynomial regressions using `numpy.polyfit`.
* **C++ Firmware Generator:** Formats the resulting polynomial coefficients directly into optimized C/C++ floats (avoiding expensive `pow()` calls to save microcontroller clock cycles).
* **Data Export & Visualization:** Automatically saves calibration dataset to CSV (`pandas`) and plots raw data points vs. fitted curve lines (`matplotlib`).

---

## 🛠️ Hardware Setup

1. **Humanoid Robot Subsystem:** Tendon-driven robotic hand/arm (e.g., Robot Walter).
2. **Sensor:** Force Sensitive Resistor (FSR) placed at the contact points for physical human-robot interaction (handshake).
3. **Data Acquisition Unit:** Arduino Nano / ESP32 sampling analog inputs and transmitting comma-separated streams over UART ($115200\text{ baud}$).
4. **Calibration Rig:** Inline load cell or mechanical dynamometer with a turnbuckle tensioner.

---

## 🚀 How to Run

### Prerequisites
Install the required Python libraries:
```bash
pip install pyserial numpy pandas matplotlib

Connect your microcontroller to your computer and verify the COM port (e.g., COM4 or /dev/ttyUSB0).

Run the calibration script:
python fsr_calibration.py

Enter the mechanical dynamometer force ($N$) in the terminal prompt for each applied load.
Type salir after registering at least 5 calibration points.
The script will export calibracion_fsr_dinamometro.csv, log the C++ firmware code snippets in your terminal, and display the curve-fitting chart.
