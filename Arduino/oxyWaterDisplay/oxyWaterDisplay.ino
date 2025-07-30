// For Wifi
#include <SPI.h>
#include <WiFiNINA.h>
// For Displays
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_LEDBackpack.h>

#include "config.h"
#include "circularCache.h"
#include "smoothing.h"

// -------------------- Variables --------------------
// For readouts when disconnected
unsigned long lastDisplayRequest{ 0 };
unsigned long displayWaitMarker{ 0 };

// For Wifi
int status{ WL_IDLE_STATUS };
WiFiServer server{ 80 };

bool reconnecting = false;
unsigned long reconnectStart = 0;

// For 7 segment displays
Adafruit_7segment tempDisplay{};
Adafruit_7segment oxyDisplay{};
Adafruit_7segment waterDisplay{};

// Smoothing
unsigned long measureWaitMarker;
Smoothing oxySmooth{};
Smoothing waterSmooth{};

// For Cache System
unsigned long cacheWaitMarker{ 0 };
CircularCache cache{};

// -------------------- Helper Functions --------------------
// ---------- Memory Allocation ----------
// Utility function to get free memory (SRAM)
extern int __heap_start, *__brkval;
int freeMemory() {
  int v;
  return (int)&v - (__brkval == 0 ? (int)&__heap_start : (int)__brkval);
}
// ---------- Text Parsing ----------
String readFromUntil(const String &text, const String &flagStart, const String &flagEnd) {
  String prev = text.substring(0, flagStart.length());
  int index = flagStart.length() - 1;
  while ((prev != flagStart) && (index < text.length())) {
    ++index;
    prev = text.substring((index - flagStart.length() + 1), (index + 1));
  }
  prev = text.substring(index, (index + flagEnd.length()));
  String result = "";
  while ((prev != flagEnd) && (index < text.length())) {
    ++index;
    result += text[index];
    prev = text.substring((index + 1), (index + flagEnd.length() + 1));
  }
  return result;
}
bool stringContains(const String &text, const String &substring) {
  for (int i = 0; i < text.length() - substring.length(); ++i) {
    if (text.substring(i, i + substring.length()) == substring) {
      return true;
    }
  }
  return false;
}

// ---------- For Sensor Measurements ----------
// calc functions just for Readouts when disconnected
// The argument "val" in the calc functions should be a 0-1024 value
double calcWater(double val) {
  double current = val / SENSE_RESISTANCE * VOLT_REF / 1023 * 1000;
  double dewPoint = ((
                       (current - WATER_LOWER_CURRENT_BOUNDS) / WATER_CURRENT_RANGE)
                     * (WATER_DEW_RANGE))
                    + WATER_LOWER_DEW_BOUNDS;
  double exponent = (13.6627 - 2720.84 / (275.38 + dewPoint));
  double ppm = pow(10, exponent);
  return ppm;
}
double calcOxy(double val) {
  return ((((val * VOLT_REF / 1023.0 / SENSE_RESISTANCE * 1000.0) - OXY_LOWER_CURRENT_BOUNDS) / OXY_CURRENT_RANGE) * OXY_PPM_RANGE) + OXY_LOWER_PPM_BOUNDS;
}
void takeMeasurements() {
  // Taking Measurements
  unsigned long oxySum = 0;
  unsigned long waterSum = 0;
  for (int i = 0; i < SMOOTH_CHUNK_SIZE; ++i) {
    oxySum += analogRead(OXY_PIN);
    waterSum += analogRead(WATER_PIN);
  }
  double oxyAvrg = static_cast<double>(oxySum) / SMOOTH_CHUNK_SIZE;
  double waterAvrg = static_cast<double>(waterSum) / SMOOTH_CHUNK_SIZE;
  oxySmooth.addValue(oxyAvrg);
  waterSmooth.addValue(waterAvrg);
}
void initSmoothing() {
  for (uint16_t i = 0; i < SMOOTH_NUM; ++i) {
    unsigned long oxySum = 0;
    unsigned long waterSum = 0;
    for (int i = 0; i < SMOOTH_CHUNK_SIZE; ++i) {
      oxySum += analogRead(OXY_PIN);
      waterSum += analogRead(WATER_PIN);
    }
    double oxyAvrg = static_cast<double>(oxySum) / SMOOTH_CHUNK_SIZE;
    double waterAvrg = static_cast<double>(waterSum) / SMOOTH_CHUNK_SIZE;
    oxySmooth.smoothArray[i] = oxyAvrg;
    oxySmooth.smoothSum += oxyAvrg;
    waterSmooth.smoothArray[i] = waterAvrg;
    waterSmooth.smoothSum += waterAvrg;
  }
}

// ---------- For Readout Displays ----------
void sevenSegPrint(Adafruit_7segment &display, const String &printMssg) {
  if (!printMssg.length()) {
    display.clear();
    display.writeDisplay();
    return;
  }
  bool isNumber = true;
  for (uint8_t i = 0; i < printMssg.length(); ++i) {
    char c = printMssg[i];
    if ((c < '0' || c > '9') && c != '.') {
      isNumber = false;
      break;
    }
  }
  if (isNumber) {
    display.print(printMssg.toFloat());
  } else {
    printChars(display, printMssg);
  }
  display.writeDisplay();
}
// Prints a string to the 7 segment displays
// For some reason, the regular print function wasn't working for me with some strings
void printChars(Adafruit_7segment &display, const String &printMssg) {
  display.clear();
  // display.writeDisplay();
  for (int i = 0; i < printMssg.length(); ++i) {
    display.writeDigitAscii(i, printMssg[i], false);
  }
  display.writeDisplay();
}
void displayWhileDisconnected() {
  tempDisplay.print("DISC");
  tempDisplay.writeDisplay();

  // checking for out of bounds current errors
  double oxyVal = oxySmooth.getValue();
  double oxyCurrent = oxyVal * 5.0 / 1023.0 / SENSE_RESISTANCE * 1000.0;
  if (oxyCurrent < OXY_LOWER_CURRENT_BOUNDS) {
    printChars(oxyDisplay, OFFSCALE_LOW_DISPLAY);
  } else if (oxyCurrent > OXY_UPPER_CURRENT_BOUNDS) {
    printChars(oxyDisplay, OFFSCALE_HIGH_DISPLAY);
  } else {
    oxyDisplay.print(calcOxy(oxySmooth.getValue()));
    oxyDisplay.writeDisplay();
  }

  double waterVal = waterSmooth.getValue();
  double waterCurrent = waterVal * 5.0 / 1023.0 / SENSE_RESISTANCE * 1000.0;
  if (waterCurrent < WATER_LOWER_CURRENT_BOUNDS) {
    printChars(waterDisplay, OFFSCALE_LOW_DISPLAY);
  } else if (waterCurrent > WATER_UPPER_CURRENT_BOUNDS) {
    printChars(waterDisplay, OFFSCALE_HIGH_DISPLAY);
  } else {
    waterDisplay.print(calcWater(waterSmooth.getValue()));
    waterDisplay.writeDisplay();
  }
}

// ---------- Wifi ----------
void printWifiStatus() {
  // print the SSID of the network you're attached to:
  Serial.print("SSID: ");
  Serial.println(WiFi.SSID());

  // print your board's IP address:
  IPAddress ip = WiFi.localIP();
  Serial.print("IP Address: ");
  Serial.println(ip);

  // print the received signal strength:
  long rssi = WiFi.RSSI();
  Serial.print("signal strength (RSSI):");
  Serial.print(rssi);
  Serial.println(" dBm");
}
void connectToWifi() {
  // check for the WiFi module:
  if (WiFi.status() == WL_NO_MODULE) {
    Serial.println("Communication with WiFi module failed!");
    // don't continue
    while (true)
      ;
  }
  String fv = WiFi.firmwareVersion();
  if (fv < WIFI_FIRMWARE_LATEST_VERSION) {
    Serial.println("Please upgrade the firmware");
  }
  // attempt to connect to WiFi network:
  while (status != WL_CONNECTED) {
    Serial.print("Attempting to connect to Network named: ");
    Serial.print(NETWORK_SSID);                  // print the network name (SSID);
    Serial.println(". Please wait 10 seconds");  // print the network name (SSID);

    // Connect to WPA/WPA2 network. Change this line if using open or WEP network:
    status = WiFi.begin(NETWORK_SSID, NETWORK_PASS);

    // wait 10 seconds for connection:
    unsigned long startTime = millis();
    measureWaitMarker = startTime;
    displayWaitMarker = startTime;
    // ----- Loop while waiting -----
    while (millis() < startTime + 10000) {
      // Starts looping for live readouts before connected
      if (millis() >= measureWaitMarker) {  // wait for controlling the sensor read timing
        takeMeasurements();
        measureWaitMarker += MEASUREMENT_DELAY;
      }
      if (millis() >= displayWaitMarker) {
        displayWhileDisconnected();
        displayWaitMarker += DISPLAY_REFRESH_RATE;
      }
    }
  }
  server.begin();     // start the web server on port 80
  printWifiStatus();  // you're connected now, so print out the status
}
void reconnectIfNeeded() {
  if (WiFi.status() == WL_CONNECTED) {
    reconnecting = false;
    return;
  }

  if (!reconnecting) {
    Serial.println("WiFi disconnected, attempting reconnect...");
    WiFi.begin(NETWORK_SSID, NETWORK_PASS);
    reconnectStart = millis();
    reconnecting = true;
  }

  if (millis() - reconnectStart >= 3000) {
    reconnecting = false;
    if (WiFi.status() == WL_CONNECTED) {
      Serial.println("WiFi reconnected.");
      server.begin();
      printWifiStatus();
    } else {
      Serial.println("WiFi reconnection failed.");
    }
  }
}
void handleWifi() {
  WiFiClient client = server.available();  // listen for incoming clients
  if (client) {                            // if you get a client,
    bool shouldRespond = false;
    String currentLine = "";      // make a String to hold incoming data from the client
    while (client.connected()) {  // loop while the client's connected
      if (client.available()) {   // if there's bytes to read from the client,
        char c = client.read();   // read a byte, then
        if (c == '\n') {          // if the byte is a newline character
          if (currentLine.length() == 0) {
            // HTTP headers always start with a response code (e.g. HTTP/1.1 200 OK)
            // and a content-type so the client knows what's coming, then a blank line:
            client.println("HTTP/1.1 200 OK");
            client.println("Content-type:text/html");
            client.println();

            // the content of the HTTP response follows the header:
            // ----- Sending Response -----
            if (shouldRespond) {
              String msg = "";
              msg += REQUEST_RECIEVED_FLAG;
              msg += CACHE_TIME_FLAG;
              msg += String{ millis() };
              msg += END_FLAG;
              client.print(msg);

              cache.send(client);

              Serial.println("\n");
            }
            // ----- End Sending Response -----

            // The HTTP response ends with another blank line:
            client.println();
            // break out of the while loop:
            break;
          } else {
            Serial.println(currentLine);
            // ----- Reading Request -----
            if (stringContains(currentLine, DATA_TRANSFER_SUCCESS_FLAG)) {
              cache.clearOldCache();
            }
            if (currentLine.startsWith(HTTP_CACHE_REQUEST_FLAG)) {
              shouldRespond = true;
            }
            if (currentLine.startsWith(HTTP_DISPLAY_FLAG)) {
              sevenSegPrint(tempDisplay, readFromUntil(currentLine, TEMP_FLAG, END_FLAG));
              sevenSegPrint(oxyDisplay, readFromUntil(currentLine, OXY_FLAG, END_FLAG));
              sevenSegPrint(waterDisplay, readFromUntil(currentLine, WATER_FLAG, END_FLAG));
              lastDisplayRequest = millis();
            }
            // ----- End Reading Request -----
            currentLine = "";
          }
        } else if (c != '\r') {  // if you got anything else but a carriage return character,
          currentLine += c;      // add it to the end of the currentLine
        }
      }
    }
    // close the connection:
    client.stop();
  }
}

// -------------------- Arduino Executing Functions --------------------
void setup() {
  // Initialize Serial
  Serial.begin(9600);

  // Print free memory
  Serial.print("Free memory at startup: ");
  Serial.println(freeMemory());

  // Initialize Segment Displays with I2C addresses
  tempDisplay.begin(TEMP_DISPLAY_ADDRESS);
  oxyDisplay.begin(OXY_DISPLAY_ADDRESS);
  waterDisplay.begin(WATER_DISPLAY_ADDRESS);

  initSmoothing();

  connectToWifi();

  cacheWaitMarker = millis();
}

void loop() {
  reconnectIfNeeded();
  if (!reconnecting) {
    handleWifi();
  }

  // ----- Adding to Cache -----
  if (millis() >= cacheWaitMarker) {
    String newCacheLog = "";
    newCacheLog += CACHE_LOG_FLAG;
    newCacheLog += CACHE_TIME_FLAG;
    newCacheLog += String{ millis() };
    newCacheLog += END_FLAG;
    newCacheLog += OXY_FLAG;
    double oxy = oxySmooth.getValue();
    newCacheLog += String{ oxy };
    newCacheLog += END_FLAG;
    newCacheLog += WATER_FLAG;
    double water = waterSmooth.getValue();
    newCacheLog += String{ water };
    newCacheLog += END_FLAG;
    cache.add(newCacheLog);
    cacheWaitMarker += CACHE_CYCLE_DELAY;
  }

  // ----- Analog Reading and Smoothing -----
  if (millis() >= measureWaitMarker) {  // wait for controlling the sensor read timing
    takeMeasurements();
    measureWaitMarker += MEASUREMENT_DELAY;
  }

  // ----- Readouts upon disconnect -----
  if (millis() - lastDisplayRequest >= DISPLAY_REQUEST_WAIT && millis() >= displayWaitMarker) {
    displayWhileDisconnected();
    displayWaitMarker += DISPLAY_REFRESH_RATE;
  }
}