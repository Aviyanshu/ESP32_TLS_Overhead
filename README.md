# Does TLS slow down an ESP32 MQTT sensor outside the lab?

This project measures what TLS 1.2 costs an ESP32 MQTT sensor in an ordinary home network rather than a laboratory. One ESP32 exchanged MQTT messages with a broker on a PC, once over plain MQTT and once over TLS, and I recorded two things: the free heap left on the device and the round-trip time of each message. Measurements were taken at three positions relative to the access point (near, medium and far). The TLS handshake was excluded deliberately, so the results describe the cost of an already established connection.

The project follows up Del-Valle-Soto et al. (2026), [*Stability-Aware Security–Performance Trade-Off Analysis in Resource-Constrained IoT Systems*](https://doi.org/10.3390/digital6020035), which measured TLS on ESP32s in a controlled lab with the handshake included and suggested that degraded wireless conditions might increase its cost. Because their latency figures include the handshake and mine do not, the two sets of numbers are not directly comparable.

A written report of the study is available on request.

![Every round trip by position, payload and protocol](figures/fig_rtt.png)

## Findings

The data consist of 1,800 round trips (900 plain, 900 TLS) from 36 independent sessions, collected on the night of 2–3 September 2026.

- **Memory.** TLS left **43.1 KB less free heap** than plain MQTT (about 19% of the plain free heap). The difference was the same in all six conditions to within 25 bytes. This is the clearest result of the study.
- **Typical latency.** TLS did not measurably slow a typical message. Medians were within 3 ms, and the small differences that were statistically detectable went in both directions. Timing used `millis()`, which has 1 ms resolution, so this means no difference at that resolution rather than zero cost.
- **Slow round trips.** Occasional messages took far longer than usual. These were about **three times as frequent** under TLS at every cutoff from 150 ms to 1 s, but because they are rare, the difference is statistically clear only at 150 and 300 ms. I report this as a pattern that needs confirmation.
- **Near versus away.** Near the access point, TLS had no trips over 300 ms; away from it, TLS had 20 and plain had 4. This grouping was chosen after seeing the data, so it is a hypothesis for a follow-up study rather than a finding.
- **Possible cause.** In both protocols the slow trips cluster at about 300 ms and 1.4 s, which is consistent with TCP retransmission timeouts. This has not yet been confirmed with a packet capture.

## Repository contents

```
ESP32/                 plain MQTT, dummy payload
ES32TLS/               MQTT over TLS 1.2, dummy payload
ESP32_TEMP/            plain MQTT, DS18B20 temperature payload
ESP32TLS_TEMP/         MQTT over TLS 1.2, DS18B20 temperature payload
loggers/               Python serial loggers that save the ESP32 output as CSV
clean/                 the 36 session CSV files used in the analysis
tls_mqtt_analysis.py   computes and prints all results
make_figures.py        produces the four figures
figures/               figures (PNG)
```

## Setup

- **Board:** ESP32 DevKit V1 (WROOM-32), Arduino framework, WiFi modem sleep disabled
- **MQTT client:** PubSubClient at QoS 0, over `WiFiClient` (plain) or `WiFiClientSecure` (TLS)
- **Broker:** Mosquitto on a Windows PC on the same LAN, port 1883 (plain) and 8883 (TLS)
- **TLS:** version 1.2, ECDHE-RSA-AES256-GCM-SHA384, self-signed CA pinned on the ESP32; server authentication only
- **Sensor:** DS18B20 on GPIO 4 (temperature sketches only)
- **Network:** a single 2.4 GHz access point. A second access point with the same network name was switched off, because the ESP32 joined either one unpredictably.

### How a measurement works

Every 3 seconds the ESP32 records `millis()` and publishes `seq,timestamp` to `sensor/test`, a topic it is also subscribed to. When the broker echoes the message back, the callback records `millis()` again; the difference is the round-trip time. This is printed over serial together with free heap and RSSI, and saved by the logger.

In the temperature sketches the timestamp is taken before the sensor read, so those round trips also include the read (about 29 ms, equal for both protocols).

Opening the serial port resets the ESP32, so each CSV file is an independent session: a fresh boot, WiFi association, MQTT connection and, for TLS, a fresh handshake.

## Reproducing the analysis

Requires Python 3 and the packages listed in `requirements.txt`.

```bash
pip install -r requirements.txt
python tls_mqtt_analysis.py   # reads clean/*.csv and prints all results
python make_figures.py        # writes the figures to figures/
```

### Data format

Files are named `<position>__<original name>.csv`, where position is `strong` (near the access point), `medium` or `weak` (far). `tls` in the name indicates a TLS session and `temp` a temperature-sensor session.

| Column | Description |
| --- | --- |
| `SEQUENCE` | Message number, 1–50 in every file. No gaps occur, so no messages were lost and no reconnections took place. |
| `RTT (ms)` | Round-trip time from `millis()` |
| `HEAP (bytes)` | Free heap when the echo arrived |
| `RSSI (dBm)` | Signal strength when the echo arrived |
| `Temperature (C)` | Temperature-sensor sessions only |
| `Wall Clock Time` | Time on the logging PC |

## Running the experiment

1. In each sketch, replace the `SSID`, `PASSWORD` and `IP` placeholders and the placeholder CA certificate with your own values. Do not commit real credentials.
2. Create a CA and a broker certificate whose Subject Alternative Name includes the broker's IP address, and configure Mosquitto's 8883 listener to use them. Paste the CA certificate into the TLS sketches.
3. Flash a sketch, set `PORT` in the matching logger to the ESP32's serial port, and run the logger. Each run records three sessions of 50 messages.
4. Check every file before analysis: sequence numbers should run from 1 to 50, RSSI should be stable, and free heap should be about 230 KB for plain or 187 KB for TLS. The heap check identifies which sketch produced a file, and caught one run recorded with the wrong sketch.

## Limitations

- `millis()` has 1 ms resolution, so the per-message encryption cost is not resolved.
- Only 15 of the 1,800 trips exceeded 500 ms, and the cutoffs and near/away grouping were chosen after seeing the data.
- Plain and TLS sessions were run in consecutive blocks rather than alternated, so changes over the evening may be confounded with protocol.
