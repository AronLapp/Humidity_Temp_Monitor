#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <Adafruit_BME280.h>
#include "secrets.h"

Adafruit_BME280 bme;

const char *serverUrl = "http://192.168.1.105:5000/measurements";
const char *nodeId = "living_room_1";

const unsigned long MEASUREMENT_INTERVAL_MS = 60UL * 1000UL;
unsigned long lastMeasurement = 0;

void setup()
{
  Serial.begin(115200);
  delay(1000);

  WiFi.setHostname(nodeId);
  WiFi.begin(WIFI_SSID2, WIFI_PASS2);
  Serial.print("Connecting to Wi-Fi");
  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWi-Fi connected");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());

  Wire.begin(21, 22);
  if (!bme.begin(0x76) && !bme.begin(0x77))
  {
    Serial.println("BME280 not found");
    while (1)
      delay(10);
  }
  Serial.println("BME280 connected");

  lastMeasurement = millis() - MEASUREMENT_INTERVAL_MS;
}

void loop()
{
  unsigned long now = millis();

  if (now - lastMeasurement < MEASUREMENT_INTERVAL_MS)
  {
    delay(100);
    return;
  }
  lastMeasurement = now;

  float t = bme.readTemperature();
  float h = bme.readHumidity();
  float p = bme.readPressure() / 100.0f;

  Serial.print("T=");
  Serial.print(t);
  Serial.print(" °C  rF=");
  Serial.print(h);
  Serial.print(" %  p=");
  Serial.print(p);
  Serial.println(" hPa");

  if (WiFi.status() == WL_CONNECTED)
  {
    HTTPClient http;
    http.begin(serverUrl);
    http.addHeader("Content-Type", "application/json");

    String json = "{";
    json += "\"node\":\"" + String(nodeId) + "\",";
    json += "\"temp\":" + String(t, 2) + ",";
    json += "\"hum\":" + String(h, 2) + ",";
    json += "\"press\":" + String(p, 2);
    json += "}";

    int code = http.POST(json);
    Serial.print("POST code: ");
    Serial.println(code);
    http.end();
  }
  else
  {
    Serial.println("Wi-Fi disconnected");
  }
}
