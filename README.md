# Does TLS slow down an ESP32 MQTT sensor outside the lab?

I wanted to know what TLS actually costs a small ESP32 sensor once it is running in a normal home, not in a lab. So I set up one ESP32 that sends MQTT messages to a broker on my PC, once with plain MQTT and once over TLS 1.2, and measured two things: how much free memory it has left, and how long each message takes to come back. I did this at three spots in my house (near the router, a medium distance away, and far from it). I left the TLS handshake out on purpose, because I wanted the cost of an already-open connection.


- **Board:** ESP32 DevKit V1 (WROOM-32), Arduino framework, WiFi modem sleep turned off
- **MQTT:** PubSubClient at QoS 0, using `WiFiClient` for plain and `WiFiClientSecure` for TLS
- **Broker:** Mosquitto on a Windows PC on the same network, port 1883 for plain and 8883 for TLS
- **TLS:** version 1.2 with ECDHE-RSA-AES256-GCM-SHA384, and my own CA certificate pinned on the ESP32. Only the broker proves who it is; the ESP32 doesn't use a client certificate.
- **Sensor:** a DS18B20 on GPIO 4, in the temperature sketches only
- **Network:** one 2.4 GHz access point. I have a second one at home with the same name, and the ESP32 kept joining different ones, so I switched it off for the tests.

### How a measurement works

Every 3 seconds the ESP32 notes the time with `millis()` and publishes `seq,timestamp` to `sensor/test`. It is also subscribed to that topic, so the broker sends the message straight back. When it arrives, the ESP32 checks the time again, and the difference is the round-trip time. It prints that, along with free heap and signal strength (RSSI), over serial, and the logger saves it.

In the temperature sketches, the time is noted before the sensor is read, so those round trips also include the sensor read (about 29 ms, the same for plain and TLS).

Opening the serial port resets the ESP32, so every CSV file is a fresh session: new boot, new WiFi connection, new MQTT connection, and for TLS a new handshake.

## Running the analysis

You need Python 3 and the packages in `requirements.txt`.

```bash
pip install -r requirements.txt
python tls_mqtt_analysis.py   # reads clean/*.csv and prints all the results
python make_figures.py        # saves the figures to figures/
```

### The data files

Each file is named `<position>__<original name>.csv`. The position is `strong` (near the router), `medium` or `weak` (far). If the name has `tls` in it, it's a TLS session; if it has `temp`, it's a temperature-sensor session.

| Column | What it is |
| --- | --- |
| `SEQUENCE` | Message number, 1 to 50 in every file. None are missing, so no messages were lost and the ESP32 never reconnected. |
| `RTT (ms)` | Round-trip time from `millis()` |
| `HEAP (bytes)` | Free heap when the message came back |
| `RSSI (dBm)` | Signal strength when the message came back |
| `Temperature (C)` | Temperature-sensor sessions only |
| `Wall Clock Time` | Time on the logging PC |

## Running the experiment yourself

1. In each sketch, put in your own WiFi name, password and broker IP in place of `SSID`, `PASSWORD` and `IP`, and replace the placeholder CA certificate. Don't commit your real details.
2. Make a CA and a broker certificate that has the broker's IP address in its Subject Alternative Name, and point Mosquitto's 8883 listener at them. Paste the CA certificate into the TLS sketches.
3. Flash a sketch, set `PORT` in the matching logger to your ESP32's serial port, and run the logger. It records three sessions of 50 messages.
4. Before analysing, check each file: sequence numbers should run 1 to 50, RSSI should stay steady, and free heap should be about 230 KB for plain or 187 KB for TLS. The heap check is how I caught a run where I had flashed the wrong sketch.

## Limitations

- `millis()` only measures whole milliseconds, so the actual encryption time per message isn't visible.
- Only 15 of the 1,800 messages took over 500 ms. I chose the cutoffs and the near/far grouping after seeing the data.
- I ran all the plain sessions and then all the TLS sessions for each condition, instead of alternating them, so anything that changed over the evening could look like a TLS effect.
- It's one board, one broker, one router, one house and one cipher suite, with only three positions and no packet capture.
- Only the broker is authenticated. I didn't test mutual TLS, TLS 1.3 or the handshake itself, so a more secure setup would probably need more than 43 KB.

## What I'd do next

- Time the TLS write with `micros()` to see the actual encryption cost.
- Capture packets on the broker PC to check whether the slow messages are TCP retransmissions.
- Run a bigger study with plain and TLS sessions alternating, and with the near/far grouping and the 300 ms cutoff decided before collecting the data.
- Add more positions, and try mutual TLS and TLS 1.3.

## A note on tools

I wrote the analysis and plotting scripts with help from AI and checked them myself. The experiment design, the hardware setup, the data collection and the debugging are my own.

Aviyanshu Adhikari · aviyanshuadhikari@gmail.com

