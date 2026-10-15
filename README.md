# Does TLS slow down an ESP32 MQTT sensor outside the lab?

An independent measurement study of what TLS 1.2 costs an ESP32 MQTT sensor in an ordinary home network: free heap and round-trip time, at three positions relative to the access point, with the TLS handshake excluded.

**Full write-up:** [`report/Adhikari_TLS_ESP32_Technical_Report.pdf`](report/Adhikari_TLS_ESP32_Technical_Report.pdf) (4 pages)

![Every round trip by position, payload and protocol](figures/fig_rtt.png)

## Results at a glance

1,800 round trips (900 plain, 900 TLS) in 36 independent sessions, collected on 2–3 September 2026.

| Finding | Result | Strength |
| --- | --- | --- |
| Memory | TLS left **43.1 KB less free heap** (18.7% of plain's free heap), the same in all six conditions within 25 bytes | Strong |
| Typical latency | Medians within 3 ms; significant shifts go in both directions | Strong, at 1 ms timer resolution |
| Slow round trips | About **3× as many** TLS trips above every cutoff from 150 ms to 1 s; significant only at 150 and 300 ms, mostly in the sensor runs | Pattern, not confirmed |
| Near vs away | No TLS excess near the access point; 20 vs 4 trips over 300 ms away from it | Hypothesis (grouping chosen after seeing the data) |
| Mechanism | Slow trips bunch at ~300 ms and ~1.4 s in both protocols, consistent with TCP retransmission timeouts | Hypothesis (no packet capture yet) |

RTT was measured with `millis()` (1 ms resolution). Per-message encryption on an open session is likely in microseconds, so "no change in typical latency" means no change *at millisecond resolution*, not zero cost.

This study builds on Del-Valle-Soto et al. (2026), [*Stability-Aware Security–Performance Trade-Off Analysis in Resource-Constrained IoT Systems*](https://doi.org/10.3390/digital6020035), which measured TLS on ESP32s in a controlled lab with the handshake included. Latency numbers are not directly comparable between the two studies.

## Repository layout

```
ESP32/                 plain MQTT, dummy payload
ES32TLS/               MQTT over TLS 1.2, dummy payload
ESP32_TEMP/            plain MQTT, DS18B20 temperature payload
ESP32TLS_TEMP/         MQTT over TLS 1.2, DS18B20 temperature payload
loggers/               Python serial loggers, one per sketch (3 sessions x 50 round trips each)
clean/                 the 36 session CSVs used in the report
tls_mqtt_analysis.py   prints every table in the report
make_figures.py        makes the four report figures
figures/               report figures (PNG)
report/                the technical report (PDF)
```

## Setup

| Component | Detail |
| --- | --- |
| Board | ESP32 DevKit V1 (WROOM-32), Arduino framework, WiFi modem sleep off |
| MQTT client | PubSubClient, QoS 0, over `WiFiClient` (plain) or `WiFiClientSecure` (TLS) |
| Broker | Mosquitto on a Windows PC on the same LAN; port 1883 plain, 8883 TLS |
| TLS | TLS 1.2, ECDHE-RSA-AES256-GCM-SHA384 (negotiated); self-signed CA pinned on the ESP32; server authentication only |
| Sensor | DS18B20 on GPIO 4 (sensor sketches only) |
| Network | One 2.4 GHz access point (a second access point was switched off to stop roaming) |

### How one measurement works

Every 3 s the ESP32 reads `millis()` and publishes `seq,timestamp` to `sensor/test`, a topic it also subscribes to. When the broker echoes the message back, the callback reads `millis()` again; the difference is the round-trip time, printed over serial with free heap and RSSI as a `DATA,...` line. The handshake happens before the first message and is not measured. In the sensor sketches the timestamp is taken before the temperature read, so sensor-run RTTs include it (about 29 ms, equally for both protocols).

Opening the serial port resets the ESP32, so every CSV is an independent session (fresh boot, WiFi association, MQTT connection and, for TLS, a fresh handshake).

## Reproducing the analysis

Requires Python 3 with the packages in `requirements.txt` (tested with pandas 3.0, NumPy 2.5, SciPy 1.18, Matplotlib 3.11).

```bash
pip install -r requirements.txt
python tls_mqtt_analysis.py   # reads clean/*.csv, prints all tables, writes D.pkl, TH.pkl, ...
python make_figures.py        # writes figures/
```

### Data format

Files are named `<position>__<original file>.csv`, where position is `strong` (near the access point), `medium` or `weak` (far). `tls` in the name means a TLS session; `temp` means a sensor session.

| Column | Meaning |
| --- | --- |
| `SEQUENCE` | Message number, 1–50 in every file (no gaps, so no lost messages or reconnects) |
| `RTT (ms)` | Round-trip time from `millis()` |
| `HEAP (bytes)` | `ESP.getFreeHeap()` when the echo arrived |
| `RSSI (dBm)` | `WiFi.RSSI()` when the echo arrived |
| `Temperature (C)` | Sensor sessions only |
| `Wall Clock Time` | Logger PC time |

## Running the experiment yourself

1. In each sketch, replace the `SSID`, `PASSWORD` and `IP` placeholders and the placeholder CA certificate. Never commit real credentials.
2. Create a CA and a broker certificate whose Subject Alternative Name contains the broker's IP address, and point Mosquitto's 8883 listener at them. Paste the CA certificate into the TLS sketches.
3. Flash a sketch, set `PORT` in the matching logger, and run it; it records three sessions of 50 round trips.
4. Check every file before analysis: sequence numbers 1–50, a steady RSSI, and the expected heap signature (about 230 KB free for plain, 187 KB for TLS).

## Limitations

- 1 ms timer resolution; the per-message encryption cost itself is not resolved.
- Only 15 of 1,800 trips exceed 500 ms; cutoffs and the near/away grouping were chosen after seeing the data.
- Plain and TLS ran in consecutive blocks, not interleaved; sensor and dummy runs were collected at different times.
- One board, broker, access point, location and cipher suite; three positions; no packet capture.
- Server-only TLS 1.2; mutual TLS, TLS 1.3 and the handshake were not measured, so 43 KB is a lower bound for a hardened setup.

## Next steps

Microsecond timestamps around the TLS write, packet capture on the broker host, a confirmatory study with interleaved sessions and the near/away grouping fixed in advance, more positions, and mutual TLS / TLS 1.3.

## Notes

The analysis and plotting scripts were written with AI assistance and checked by the author; the experiment design, hardware setup, data collection and debugging are the author's own.

Aviyanshu Adhikari · aviyanshuadhikari@gmail.com
