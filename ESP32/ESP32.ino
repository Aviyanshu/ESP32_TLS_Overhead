#include <WiFi.h>
#include <PubSubClient.h>

const char* SSID = "SSID";
const char* PASSWORD = "PASSWORD";
const char* mqtt_server = "IP";
const int mqtt_port = 1883;

const char* mqtt_topic = "sensor/test";

unsigned long lastPublished = 0;

WiFiClient espClient;
PubSubClient client(espClient);

void onMessage(char* topic, byte* payload, unsigned int length) {
  unsigned long now = 0;
  if (String(topic) == mqtt_topic) {
    now = millis();
  }

  char cleanPayload[length+1];

  memcpy(cleanPayload, payload, length);
  cleanPayload[length] = '\0';

  char* seqStr = strtok(cleanPayload, ",");
  char* timeStr = strtok(NULL,",");
  unsigned long heap = ESP.getFreeHeap();
  int rssi = WiFi.RSSI();

  if (seqStr != NULL && timeStr != NULL) {
    int sequenceNumber = atoi(seqStr);
    unsigned long timeReceived = strtoul(timeStr, NULL, 10);
    unsigned long rtt = now - timeReceived;
    Serial.println("DATA," + String(sequenceNumber) + "," + String(rtt) + "," + String(heap) + "," + String(rssi));
  }
}

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  WiFi.begin(SSID,PASSWORD);
  WiFi.setSleep(false);
  while ( WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("WiFi Connected. IP Address:" + WiFi.localIP().toString());

  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(onMessage);
}

void reconnect() {
  while (!client.connected()) {
    if (WiFi.status() != WL_CONNECTED) {
      Serial.println("WiFi lost — reconnecting WiFi first...");
      WiFi.reconnect();
      delay(3000);
      continue;  // skip MQTT attempt until WiFi is actually back
    }
    Serial.print("Connecting to the broker.......");
    String clientId = "esp32_temp_sensor" + String(WiFi.macAddress());
    if (client.connect(clientId.c_str())) {
      Serial.println("Connected!");
      client.subscribe(mqtt_topic);
      Serial.println("Subribed to topic:" + String(mqtt_topic));
    } else {
      Serial.print("Failed, rc=");
      Serial.print(client.state());
      Serial.println("Retrying...");
      delay(2000);
    }
  }
}

void loop() {
  // put your main code here, to run repeatedly:
  static int seq = 0;
  if(!client.connected()) {
    reconnect();
    seq = 0;
  }
  client.loop();

  unsigned long now = millis();
  if ( now - lastPublished > 3000) {
    seq++;

    lastPublished = now;

    String message = String(seq) + "," + String(now);
    client.publish(mqtt_topic, message.c_str());

    Serial.println("Published to topic:" + String(mqtt_topic));
  }
}
