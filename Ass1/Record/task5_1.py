
import time
import serial
import numpy as np
import pandas as pd

PORT = "COM5"
BAUD = 230400

SAMPLE_RATE = 5000
CAPTURE_SECONDS = 100

ser = serial.Serial(PORT, BAUD, timeout=0.1)

time.sleep(1)
ser.reset_input_buffer()

print("Capturing Morse signal...")

byte_buffer = bytearray()
raw_samples = []

start_time = time.perf_counter()

try:
    while time.perf_counter() - start_time < CAPTURE_SECONDS:

        chunk = ser.read(ser.in_waiting or 4096)

        if chunk:
            byte_buffer.extend(chunk)

        # Process complete 16-bit words
        usable_length = len(byte_buffer) - (len(byte_buffer) % 2)

        if usable_length >= 2:

            data = byte_buffer[:usable_length]
            del byte_buffer[:usable_length]

            packets = np.frombuffer(data, dtype="<u2")

            # Validate bit 15
            valid = (packets & 0x8000) != 0

            # Extract 10-bit ADC values
            adc_values = packets[valid] & 0x03FF

            raw_samples.extend(adc_values.tolist())

finally:
    elapsed = time.perf_counter() - start_time
    ser.close()

# Convert to numpy array
samples = np.array(raw_samples, dtype=np.uint16)

if len(samples) == 0:
    raise RuntimeError("No valid samples received!")

# Create time axis
time_axis = np.arange(len(samples)) / SAMPLE_RATE

# Create DataFrame
df = pd.DataFrame({
    "sample": np.arange(len(samples)),
    "time_s": time_axis,
    "ADC": samples
})

# Save data
df.to_csv("Morse_raw_data.csv", index=False)

# Summary
print("\nCapture complete")
print(f"Samples: {len(samples)}")
print(f"Duration: {elapsed:.2f} s")
print(f"Average sample rate: {len(samples)/elapsed:.2f} Hz")
print(f"Minimum ADC: {samples.min()}")
print(f"Maximum ADC: {samples.max()}")
print(f"Mean ADC: {samples.mean():.2f}")
print("Saved to Morse_raw_data.csv")
