#include <DHTesp.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include "RTClib.h"
#include <ArduinoJson.h>

#define LDR_PIN 34
#define DHT_PIN 15
#define LED_PIN 2
// Set to false if your LED is active-high (HIGH = ON). On many ESP32 boards, the on-board LED on GPIO2 is active-high.
// Change this to match your hardware setup.
static const bool LED_ACTIVE_LOW = false;

RTC_DS1307 rtc;
DHTesp dht;

const char *ssid = "Wokwi-GUEST";
const char *password = "";
const char *mqtt_server = "broker.hivemq.com";

// MQTT topics
static const char *MQTT_DATA_TOPIC = "152023003/pemiot/data";           // publishes sensor data (already used)
static const char *MQTT_LED_CMD_TOPIC = "152023003/pemiot/cmd/state/led";     // subscribe here for LED commands
static const char *MQTT_LED_STATE_TOPIC = "152023003/pemiot/state/led"; // publishes LED state after changes

WiFiClient espClient;
PubSubClient client(espClient);

unsigned long lastMsg = 0;

// Track current LED state for publishing and idempotence
volatile bool ledIsOn = false;

void applyLedState(bool turnOn)
{
  ledIsOn = turnOn;
  int level;
  if (LED_ACTIVE_LOW)
  {
    level = turnOn ? LOW : HIGH;
  }
  else
  {
    level = turnOn ? HIGH : LOW;
  }
  digitalWrite(LED_PIN, level);
}

void publishLedState(bool retained = true)
{
  const char *state = ledIsOn ? "ON" : "OFF";
  client.publish(MQTT_LED_STATE_TOPIC, state, retained);
}

void setup_wifi()
{ // perintah koneksi wifi
  delay(10);
  // We start by connecting to a WiFi network
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.mode(WIFI_STA);        // setting wifi chip sebagai station/client
  WiFi.begin(ssid, password); // koneksi ke jaringan wifi

  while (WiFi.status() != WL_CONNECTED)
  { // perintah tunggu esp32 sampi terkoneksi ke wifi
    delay(500);
    Serial.print(".");
  }

  randomSeed(micros());

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

void callback(char *topic, byte *payload, unsigned int length)
{ // perintah untuk menampilkan data ketika esp32 di setting sebagai subscriber
  // Copy payload to a temporary String for easier parsing
  String msg;
  msg.reserve(length);
  for (unsigned int i = 0; i < length; i++)
  {
    msg += (char)payload[i];
  }

  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  Serial.println(msg);

  // Handle LED command topic only
  if (String(topic) == MQTT_LED_CMD_TOPIC)
  {
    String cmd = msg;
    cmd.trim();
    cmd.toUpperCase();

    bool recognized = true;

    if (cmd == "1" || cmd == "ON")
    {
      applyLedState(true);
    }
    else if (cmd == "0" || cmd == "OFF")
    {
      applyLedState(false);
    }
    else if (cmd == "TOGGLE")
    {
      applyLedState(!ledIsOn);
    }
    else
    {
      // Optional: accept simple JSON {"state":"ON"}
      // Try to parse JSON minimally
      JsonDocument j;
      DeserializationError err = deserializeJson(j, msg);
      if (!err && j.containsKey("state"))
      {
        String st = j["state"].as<String>();
        st.trim();
        st.toUpperCase();
        if (st == "ON")
          applyLedState(true);
        else if (st == "OFF")
          applyLedState(false);
        else
          recognized = false;
      }
      else
      {
        recognized = false;
      }
    }

    if (!recognized)
    {
      Serial.println("Unrecognized LED command. Use: ON, OFF, 1, 0, TOGGLE or {\"state\":\"ON|OFF\"}");
      return;
    }

    // Publish current LED state (retained) so new subscribers get last known state
    publishLedState(true);
    Serial.print("LED is now: ");
    Serial.println(ledIsOn ? "ON" : "OFF");
  }
}

void reconnect()
{ // perintah koneksi esp32 ke mqtt broker baik itu sebagai publusher atau subscriber
  // Loop until we're reconnected
  while (!client.connected())
  {
    Serial.print("Attempting MQTT connection...");
    // perintah membuat client id agar mqtt broker mengenali board yang kita gunakan
    String clientId = "ESP32Client-";
    clientId += String(random(0xffff), HEX);
    // Attempt to connect
    if (client.connect(clientId.c_str()))
    {
      Serial.println("Connected");
      // Subscribe to LED command topic and publish current state
      client.subscribe(MQTT_LED_CMD_TOPIC);
      publishLedState(true); // publish retained current LED state
    }
    else
    {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      // Wait 5 seconds before retrying
      delay(5000);
    }
  }
}

void setup()
{
  // put your setup code here, to run once:
  Serial.begin(115200);

  setup_wifi();

  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);

  pinMode(LDR_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);
  // Initialize LED OFF
  applyLedState(false);
  dht.setup(DHT_PIN, DHTesp::DHT22);

  if (!rtc.begin())
  {
    Serial.println("Couldn't find RTC");
    Serial.flush();
    abort();
  }

  if (!rtc.isrunning())
  {
    Serial.println("RTC is NOT running, let's set the time!");
    rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
  }
}

void loop()
{
  // put your main code here, to run repeatedly:

  if (!client.connected())
  {
    reconnect();
  }
  client.loop();

  unsigned long now = millis();
  if (now - lastMsg > 2000)
  {
    lastMsg = now;

    int lightlevel = analogRead(LDR_PIN);
    TempAndHumidity data = dht.getTempAndHumidity();
    DateTime time = rtc.now();

    JsonDocument doc;
    doc["temperature"] = data.temperature;
    doc["humidity"] = data.humidity;
    doc["lightlevel"] = lightlevel;
    doc["datetime"] = time.timestamp(DateTime::TIMESTAMP_FULL);

    String jsonData;
    serializeJson(doc, jsonData);

    client.publish(MQTT_DATA_TOPIC, jsonData.c_str());
    Serial.println("Sending data: ");
    Serial.println(jsonData);
  }

  delay(1000); // this speeds up the simulation
}
