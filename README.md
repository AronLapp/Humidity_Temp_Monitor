# Humidity_Temp_Monitor

Distributed monitoring platform using ESP32+BME280 sensor nodes for temperature and humidity tracking. A Raspberry Pi collects all data, provides visualizations via a local web server and triggers alerts when values surpass limits.

## Setup ESP Boards

To connect the ESP32 sensor stations to to Wi-Fi, SSID and Password must be stored in a file. At this moment, the main.cpp file imports these from ```ESP32/include/secrets.h```, which is not added to this repository. This file needs to be created individually.

### Example configuration of ```secrets.h```

```hpp
#pragma once

static const char *WIFI_SSID = "YOUR_SSID";
static const char *WIFI_PASS = "YOUR_PASSWORD";
```
