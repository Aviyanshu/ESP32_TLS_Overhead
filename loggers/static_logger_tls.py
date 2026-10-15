import serial
import csv
import time
import statistics

PORT = "COM5"
BAUD = 115200
MAX_TRIALS = 50
NUM_RUNS = 3

def run_trial(run_number):
    output_file = f"mqtt_base_tls_dataset_{run_number}.csv"
    ser = serial.Serial(PORT, BAUD, timeout=2)
    time.sleep(5)  # let the ESP32 finish resetting after the serial port opens

    rtts = []
    print(f"\n=== Run {run_number}: listening on {PORT} at {BAUD} baud ===")

    with open(output_file, mode='w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["SEQUENCE", "RTT (ms)", "HEAP (bytes)", "RSSI (dBm)", "Wall Clock Time"])
        csvfile.flush()

        while len(rtts) < MAX_TRIALS:
            line = ser.readline().decode('utf-8', errors="ignore").strip()

            if line:
                print(f"Received: {line}")

            if line.startswith("DATA,"):
                parts = line.split(",")
                if len(parts) == 5:
                    sequence, rtt, heap, rssi = parts[1], parts[2], parts[3], parts[4] if len(parts) > 4 else None
                    writer.writerow([sequence, rtt, heap, rssi, time.strftime("%Y-%m-%d %H:%M:%S")])
                    csvfile.flush()
                    rtts.append(int(rtt))
                    print(f"Trial {len(rtts)}: seq={sequence}, rtt={rtt}ms, heap={heap}, rssi={rssi}")

    ser.close()

    print(f"\n--- Run {run_number} Summary ---")
    print(f"Mean:   {statistics.mean(rtts):.2f} ms")
    print(f"Median: {statistics.median(rtts):.2f} ms")
    print(f"StdDev: {statistics.stdev(rtts):.2f} ms")
    print(f"Min/Max: {min(rtts)} / {max(rtts)} ms")
    print(f"Saved to {output_file}")

def main():
    for run_number in range(1, NUM_RUNS + 1):
        run_trial(run_number)
        if run_number < NUM_RUNS:
            print(f"\nRun {run_number} complete. Ready to start run {run_number + 1}...")

if __name__ == "__main__":
    main()