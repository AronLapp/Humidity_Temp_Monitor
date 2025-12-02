#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <Adafruit_BME280.h>
#include "secrets.h"

Adafruit_BME280 bme;

const char *serverUrl = "http://192.168.1.107:5000/measurements";

const char *nodeId = "living_room_1";

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
}

void loop()
{
  const int samples = 60;

  double sumT = 0.0;
  double sumH = 0.0;
  double sumP = 0.0;

  for (int i = 0; i < samples; i++)
  {
    float t = bme.readTemperature();
    float h = bme.readHumidity();
    float p = bme.readPressure() / 100.0f;

    sumT += t;
    sumH += h;
    sumP += p;

    delay(1000);
  }

  float avgT = sumT / samples;
  float avgH = sumH / samples;
  float avgP = sumP / samples;

  Serial.print("AVG T=");
  Serial.print(avgT);
  Serial.print(" °C  AVG rF=");
  Serial.print(avgH);
  Serial.print(" %  AVG p=");
  Serial.print(avgP);
  Serial.println(" hPa");

  if (WiFi.status() == WL_CONNECTED)
  {
    HTTPClient http;
    http.begin(serverUrl);
    http.addHeader("Content-Type", "application/json");

    String json = "{";
    json += "\"node\":\"" + String(nodeId) + "\",";
    json += "\"temp\":" + String(avgT, 2) + ",";
    json += "\"hum\":" + String(avgH, 2) + ",";
    json += "\"press\":" + String(avgP, 2);
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