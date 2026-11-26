import time
import numpy as np
import serial

PORT = "/COM6"
BAUD = 230400
TARGET_CAPTURE_SECONDS = 95.0


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
    print(f"Capturing target duration: {TARGET_CAPTURE_SECONDS} seconds\n")

    try:
        while True:
            now = time.time()
            elapsed = now - start_time
            if elapsed >= TARGET_CAPTURE_SECONDS:
                break

            # 1. Read available data chunk from serial
            chunk = ser.read(ser.in_waiting or 4096)
            if chunk:
                byte_buf.extend(chunk)
                total_bytes_read += len(chunk)

            # 2. Parse complete 16-bit frame words
            if len(byte_buf) >= 2:
                even_len = (len(byte_buf) // 2) * 2
                data_chunk = byte_buf[:even_len]
                byte_buf = byte_buf[even_len:]

                # Protocol frame: 16-bit uint (0x8000 bit checks validity, 0x03FF masks 10-bit ADC)
                arr = np.frombuffer(data_chunk, dtype=np.uint16)
                valid_mask = (arr & 0x8000) == 0x8000
                valid_adc = arr[valid_mask] & 0x03FF
                raw_samples.extend(valid_adc)

            # 3. Live status updates
            # Note that this part is just to show that this "hint" is working. It is not required
            # in your own implementation.
            if now - last_update_time >= 0.2:
                last_update_time = now
                current_samples = len(raw_samples)
                current_freq = current_samples / elapsed if elapsed > 0 else 0.0
                print(
                    f"\r[STREAMING] Elapsed: {elapsed:5.1f}s / {TARGET_CAPTURE_SECONDS:.1f}s | "
                    f"Bytes: {total_bytes_read:,} | Valid Samples: {current_samples:,} | "
                    f"Rate: {current_freq:6.1f} Hz",
                    end="",
                    flush=True,
                )

    finally:
        ser.close()

    total_elapsed = time.time() - start_time
    samples_array = np.array(raw_samples, dtype=np.float64)

    # 4. Data Summary & Telemetry
    # Note that this part is just to show that this "hint" is working. It is not required
    # in your own implementation.
    print("\n\n" + "=" * 45)
    print("               CAPTURE SUMMARY               ")
    print("=" * 45)
    print(f"Total Bytes Read     : {total_bytes_read:,} bytes")
    print(f"Total Valid Samples  : {len(samples_array):,}")
    print(f"Total Time Elapsed   : {total_elapsed:.2f} seconds")

    if len(samples_array) > 0:
        avg_sample_rate = len(samples_array) / total_elapsed
        print(f"Average Sample Rate  : {avg_sample_rate:.2f} Hz")
        print(f"Min ADC Value        : {np.min(samples_array):.0f}")
        print(f"Max ADC Value        : {np.max(samples_array):.0f}")
        print(f"Mean ADC Value       : {np.mean(samples_array):.2f}")
    else:
        print("No valid ADC samples were captured.")
        return

    print("=" * 45)

if __name__ == "__main__":
    main()
