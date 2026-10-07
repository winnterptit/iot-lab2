#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>
#include <ArduinoJson.h>
#include <time.h>

#define DHTPIN 4
#define DHTTYPE DHT22
#define LDRPIN 34

// --- WiFi mo phong Wokwi ---
const char* ssid = "Wokwi-GUEST";
const char* password = "";

// --- MQTT Broker ---
// Docker Desktop (Windows/macOS): dung host.docker.internal
// Neu khong ket noi duoc, thay bang IP LAN cua may ban
const char* mqtt_server = "host.docker.internal";
const int mqtt_port = 1883;
const char* mqtt_topic = "iot/class/lab2/esp32-01/data";

WiFiClient espClient;
PubSubClient client(espClient);
DHT dht(DHTPIN, DHTTYPE);

void syncTime() {
  configTime(0, 0, "pool.ntp.org", "time.nist.gov");
  Serial.print("Dong bo NTP");
  time_t now = time(nullptr);
  while (now < 24 * 3600) {
    delay(200);
    Serial.print(".");
    now = time(nullptr);
  }
  Serial.println(" OK");
}

void setup() {
  Serial.begin(115200);
  delay(500);
  dht.begin();

  Serial.print("Ket noi WiFi");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println(" OK");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());

  syncTime();

  client.setServer(mqtt_server, mqtt_port);
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Ket noi MQTT...");
    if (client.connect("ESP32Lab2")) {
      Serial.println(" OK");
    } else {
      Serial.print(" loi rc=");
      Serial.print(client.state());
      Serial.println(", thu lai sau 2s");
      delay(2000);
    }
  }
}

void loop() {
  if (!client.connected()) reconnect();
  client.loop();

  float temp = dht.readTemperature();
  float hum = dht.readHumidity();
  int light = analogRead(LDRPIN);

  if (isnan(temp) || isnan(hum)) {
    Serial.println("Doc cam bien loi, bo qua");
    delay(2000);
    return;
  }

  StaticJsonDocument<256> doc;
  doc["device_id"] = "esp32-01";
  doc["ts"] = (double)time(nullptr);
  doc["temperature"] = round(temp * 10) / 10.0;
  doc["humidity"] = round(hum * 10) / 10.0;
  doc["light"] = light;

  char payload[256];
  serializeJson(doc, payload);
  client.publish(mqtt_topic, payload);
  Serial.print("Published: ");
  Serial.println(payload);

  delay(5000);
}
