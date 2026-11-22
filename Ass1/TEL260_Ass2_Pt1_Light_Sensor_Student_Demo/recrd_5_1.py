
import time
import numpy as np
import pandas as pd
import serial

PORT = "COM6"
BAUD = 230400
TARGET_CAPTURE_SECONDS = 95.0 * 2
FILENAME = "LDR_5.1_data2.csv"


def main():
    try:
        ser = serial.Serial(PORT, BAUD, timeout=0.01)
    except Exception as e:
        print(f"Error opening serial port {PORT}: {e}")
        return

    raw_samples = []
    byte_buf = bytearray()
    total_bytes_read = 0

    start_time = time.time()
    last_update_time = start_time

    print(f"Streaming data from {PORT} at {BAUD} baud...")
    print(f"Capturing for {TARGET_CAPTURE_SECONDS} seconds.\n")

    try:
        while True:
            now = time.time()
            elapsed = now - start_time

            if elapsed >= TARGET_CAPTURE_SECONDS:
                break

            # Read available serial data
            chunk = ser.read(ser.in_waiting or 4096)

            if chunk:
                byte_buf.extend(chunk)
                total_bytes_read += len(chunk)

            # Decode complete 16-bit words
            if len(byte_buf) >= 2:
                even_len = (len(byte_buf) // 2) * 2

                data_chunk = byte_buf[:even_len]
                del byte_buf[:even_len]

                # Arduino sends uint16 values, little-endian
                arr = np.frombuffer(data_chunk, dtype="<u2")

                # Bit 15 indicates a valid sample
                valid_mask = (arr & 0x8000) != 0

                # Extract the 10-bit ADC value
                valid_adc = arr[valid_mask] & 0x03FF

                raw_samples.extend(valid_adc.tolist())

            # Live status update
            if now - last_update_time >= 0.2:
                last_update_time = now

                current_samples = len(raw_samples)
                current_freq = (
                    current_samples / elapsed if elapsed > 0 else 0.0
                )

                print(
                    f"\r[STREAMING] Elapsed: {elapsed:5.1f}s / "
                    f"{TARGET_CAPTURE_SECONDS:.1f}s | "
                    f"Bytes: {total_bytes_read:,} | "
                    f"Valid Samples: {current_samples:,} | "
                    f"Rate: {current_freq:6.1f} Hz",
                    end="",
                    flush=True,
                )

    finally:
        ser.close()

    total_elapsed = time.time() - start_time

    samples_array = np.array(raw_samples, dtype=np.uint16)

    print("\n\n" + "=" * 45)
    print("               CAPTURE SUMMARY")
    print("=" * 45)

    print(f"Total Bytes Read     : {total_bytes_read:,} bytes")
    print(f"Total Valid Samples  : {len(samples_array):,}")
    print(f"Total Time Elapsed   : {total_elapsed:.2f} seconds")

    if len(samples_array) == 0:
        print("No valid ADC samples were captured.")
        return

    avg_sample_rate = len(samples_array) / total_elapsed

    print(f"Average Sample Rate  : {avg_sample_rate:.2f} Hz")
    print(f"Min ADC Value        : {np.min(samples_array)}")
    print(f"Max ADC Value        : {np.max(samples_array)}")
    print(f"Mean ADC Value       : {np.mean(samples_array):.2f}")

    print("=" * 45)

    # Save data to CSV
    df = pd.DataFrame({
        "sample": np.arange(len(samples_array)),
        "time_s": np.arange(len(samples_array)) / avg_sample_rate,
        "ADC": samples_array
    })

    df.to_csv(FILENAME, index=False)

    print(f"\nData saved to: {FILENAME}")
    print(f"Saved {len(df):,} valid samples.")


if __name__ == "__main__":
    main()
