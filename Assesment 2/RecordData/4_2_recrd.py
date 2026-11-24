
import serial
import numpy as np
import pandas as pd
import time

# ==========================================
# CONFIGURATION
# ==========================================

PORT = "COM6"           # Change to your Arduino COM port
BAUD_RATE = 921600

SAMPLE_RATE = 10000     # Nominal sampling rate (Hz)
DURATION = 70           # Recording duration (seconds)

FILENAME = "LDR_4.2_data.csv"

# ==========================================
# CONNECT TO ARDUINO
# ==========================================

print("Connecting to Arduino...")

ser = serial.Serial(
    port=PORT,
    baudrate=BAUD_RATE,
    timeout=0.1
)

# Arduino may reset when serial connection opens
time.sleep(2)

ser.reset_input_buffer()

print("Connection established.")
print("Starting recording...")
print("Keep the LED and LDR in a fixed position.")

# ==========================================
# RECORD DATA
# ==========================================

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

# ==========================================
# DECODE BINARY DATA
# ==========================================

# Each measurement consists of:
# 2 bytes ADC + 2 bytes duty cycle = 4 bytes

usable_length = len(raw_bytes) - (len(raw_bytes) % 4)

if usable_length == 0:
    raise RuntimeError("No valid data received from Arduino.")

records = np.frombuffer(
    raw_bytes[:usable_length],
    dtype="<u2"
).copy()

records = records.reshape(-1, 2)

adc_values = records[:, 0]
duty_values = records[:, 1]

# ==========================================
# CREATE DATAFRAME
# ==========================================

df = pd.DataFrame({

    "sample": np.arange(len(records)),

    "time_s": np.arange(len(records)) / SAMPLE_RATE,

    "ADC": adc_values,

    "duty_cycle": duty_values

})

# ==========================================
# VALIDATE DATA
# ==========================================

invalid_adc = (df["ADC"] > 1023).sum()

invalid_duty = (df["duty_cycle"] > 100).sum()

actual_sample_rate = len(df) / elapsed

print("\n========== RECORDING SUMMARY ==========")

print(f"Recording duration: {elapsed:.2f} s")
print(f"Samples received:   {len(df)}")
print(f"Average data rate:  {actual_sample_rate:.1f} Hz")

print(f"Invalid ADC values: {invalid_adc}")
print(f"Invalid duty values:{invalid_duty}")

print("=======================================\n")

if invalid_adc > 0 or invalid_duty > 0:

    raise RuntimeError(
        "Invalid values detected. Check serial connection and data format."
    )

# ==========================================
# SAVE CSV
# ==========================================

df.to_csv(FILENAME, index=False)

print(f"Data successfully saved to: {FILENAME}")

print("\nFirst five measurements:")
print(df.head())

print("\nDuty cycle values recorded:")
print(sorted(df["duty_cycle"].unique()))
