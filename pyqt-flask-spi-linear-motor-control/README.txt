# PyQt-Flask SPI Linear Motor Control

This project is a GUI-based linear motor control system using PyQt6, Flask, SPI communication, and Arduino firmware.

The system allows the user to input motor velocity, control motor direction, start or stop the motor, and monitor the current motor position through a desktop GUI.

## System Overview

```text
PyQt6 UI → Flask Server → SPI Communication → Arduino → Motor Driver → Linear Motor