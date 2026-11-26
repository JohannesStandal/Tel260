
import serial
import numpy as np
import pandas as pd
import time

# Configuration
SERIAL_PORT = "COM7"
BAUD_RATE = 921600
DURATION = 20
SAMPLE_RATE = 5000

# filename = "TEMP__measurements_cold.csv"# 20s
filename = "TEMP__measurements_hot.csv"  # 20s
# filename = "TEMP__measurements_rise.csv" # 20s
# filename = "TEMP__measurements_fall.csv" # 20s

# Open serial connection
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.01)
    time.sleep(2)
    ser.reset_input_buffer()

except serial.SerialException as e:
    print(f"Error opening serial port {SERIAL_PORT}: {e}")
    raise SystemExit(1)

print("Recording started...")

raw_bytes = bytearray()
start_time = time.perf_counter()

try:
    while time.perf_counter() - start_time < DURATION:

        chunk = ser.read(ser.in_waiting or 4096)

        if chunk:
            raw_bytes.extend(chunk)

finally:
    elapsed = time.perf_counter() - start_time
    ser.close()

print("Recording finished.")

# Decode binary uint16 values
usable_length = len(raw_bytes) - (len(raw_bytes) % 2)

samples = np.frombuffer(
    raw_bytes[:usable_length],
    dtype="<u2"
).copy()

if len(samples) == 0:
    raise RuntimeError("No samples received!")

# Time axis
time_axis = np.arange(len(samples)) / SAMPLE_RATE

# DataFrame
df = pd.DataFrame({
    "sample": np.arange(len(samples)),
    "time_s": time_axis,
    "ADC": samples
})

# Save CSV
df.to_csv(filename, index=False)

# Summary
actual_rate = len(samples) / elapsed

print(f"Samples captured: {len(samples)}")
print(f"Recording duration: {elapsed:.2f} s")
print(f"Average sample rate: {actual_rate:.1f} Hz")
print(f"Minimum ADC: {samples.min()}")
print(f"Maximum ADC: {samples.max()}")
print(f"Saved to: {filename}")
