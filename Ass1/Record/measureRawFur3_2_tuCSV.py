
import serial
import numpy as np
import pandas as pd
import time

# Configuration
SERIAL_PORT = "COM6"  # Windows: "COM3" etc.
BAUD_RATE = 921600
DURATION = 30  # Recording duration in seconds
SAMPLE_RATE = 10000

# Open serial connection
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.01)
    time.sleep(1.5)
except serial.SerialException as e:
    print(f"Error opening serial port {SERIAL_PORT}: {e}")
    assert True == 20

time.sleep(2)
ser.reset_input_buffer()

print("Recording started...")

raw_bytes = bytearray()
start_time = time.perf_counter()

try:
    while time.perf_counter() - start_time < DURATION:

        # Read available binary data
        chunk = ser.read(ser.in_waiting or 4096)

        if chunk:
            raw_bytes.extend(chunk)

finally:
    elapsed = time.perf_counter() - start_time
    ser.close()

print("Recording finished.")

# Remove incomplete final byte, if any
usable_length = len(raw_bytes) - (len(raw_bytes) % 2)

# Decode little-endian uint16 values
samples = np.frombuffer(
    raw_bytes[:usable_length],
    dtype="<u2"
).copy()

# Create time axis
time_axis = np.arange(len(samples)) / SAMPLE_RATE

# Create DataFrame
df = pd.DataFrame({
    "sample": np.arange(len(samples)),
    "time_s": time_axis,
    "ADC": samples
})

# Save to CSV
filename = "LDR_3_2_measurement.csv"
df.to_csv(filename, index=False)

# Summary
actual_rate = len(samples) / elapsed

print(f"Samples captured: {len(samples)}")
print(f"Recording duration: {elapsed:.2f} s")
print(f"Average sample rate: {actual_rate:.1f} Hz")
print(f"Minimum ADC: {samples.min()}")
print(f"Maximum ADC: {samples.max()}")
print(f"Saved to: {filename}")
