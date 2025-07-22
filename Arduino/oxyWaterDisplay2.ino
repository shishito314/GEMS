// For Wifi
#include <SPI.h>
#include <WiFiNINA.h>
// For Displays
#include <Wire.h>
#include <Adafruit_GFX.h>
#include "Adafruit_LEDBackpack.h"

// -------------------- Constants (Must Match Python) --------------------
// For HTTP Communication
// NOTE: Make sure none of these flags are contained within the other flags, as it will mess up text parsing
#define TEMP_FLAG "Temp:"  //                                                                        MUST MATCH PYTHON
#define OXY_FLAG "Oxy:" //                                                                           MUST MATCH PYTHON
#define WATER_FLAG "Water:" //                                                                       MUST MATCH PYTHON

// For Cache System
#define CACHE_LOG_FLAG "Log:" //                                                                     MUST MATCH PYTHON
#define REQUEST_RECIEVED_FLAG "Received" //                                                          MUST MATCH PYTHON
#define DATA_TRANSFER_SUCCESS_FLAG "Success" //                                                      MUST MATCH PYTHON
#define CACHE_REQUEST_FLAG "Log_"
#define CACHE_TIME_FLAG "Time:" //                                                                   MUST MATCH PYTHON

// Misc. Communication Flags
#define DISPLAY_FLAG "Display_" //                                                                   MUST MATCH PYTHON
#define DISPLAY_ERROR_MESSAGE "Error" //                                                             MUST MATCH PYTHON

#define END_FLAG "End" //                                                                            MUST MATCH PYTHON

// -------------------- Other Constants --------------------
// ---------- May Be Changed ----------
#define NETWORK_SSID "ChiangGroupWifi"  // your network SSID (name)
#define NETWORK_PASS "EVs4ALL!"  // your network password (using WPA)

// For Readouts On Disconnect
#define DISPLAY_REQUEST_WAIT 8000  // how long to wait for the HTTP request before changing to on-arduino calculation + readout
#define DISPLAY_REFRESH_RATE 250

// For Sensor Calculations
#define WATER_LOWER_CURRENT_BOUNDS 4
#define WATER_UPPER_CURRENT_BOUNDS 20
#define WATER_LOWER_DEW_BOUNDS -100 // regular int8_t because it's negative
#define WATER_UPPER_DEW_BOUNDS 20

#define OXY_LOWER_CURRENT_BOUNDS 4
#define OXY_UPPER_CURRENT_BOUNDS 20
#define OXY_LOWER_PPM_BOUNDS 0
#define OXY_UPPER_PPM_BOUNDS 100 // this is a uint16_t so we can set the oxygen sensor output range to higher than 256

#define SENSE_RESISTANCE 220 // The resistance used for calculating current from the Water and Oxygen Sensors
#define VOLT_REF 5

// Analog Reading Pins
#define OXY_PIN A1 // The analog pin connected to the Oxygen Sensor
#define WATER_PIN A0 // The same, for the water sensor

// For Digital Filter (Moving Average)
#define MEASUREMENT_DELAY 0  // as quick a sample rate as possible
#define SAMPLE_RATE_DELAY 150 // microseconds
#define SMOOTH_NUM 20
#define SMOOTH_CHUNK_SIZE 125

// For Cache System
#define CACHE_CYCLE_DELAY 5000
#define CACHE_MAX 20

#define OFFSCALE_HIGH_DISPLAY "HI" // For displays when disconnected
#define OFFSCALE_LOW_DISPLAY "LO" // For displays when disconnected

#define TEMP_DISPLAY_ADDRESS 0x70
#define OXY_DISPLAY_ADDRESS 0x71
#define WATER_DISPLAY_ADDRESS 0x72

// ---------- Should Not Change ----------
// HTTP Communcation Flags (For internal use)
const String HTTP_DISPLAY_FLAG = String{"GET /"} + DISPLAY_FLAG;
const String HTTP_CACHE_REQUEST_FLAG = String{"GET /"} + CACHE_REQUEST_FLAG;

// For Calculating Sensor Measurement (Internal Use)
#define WATER_CURRENT_RANGE WATER_UPPER_CURRENT_BOUNDS - WATER_LOWER_CURRENT_BOUNDS
#define WATER_DEW_RANGE WATER_UPPER_DEW_BOUNDS - WATER_LOWER_DEW_BOUNDS
#define OXY_CURRENT_RANGE OXY_UPPER_CURRENT_BOUNDS - OXY_LOWER_CURRENT_BOUNDS
#define OXY_PPM_RANGE OXY_UPPER_PPM_BOUNDS - OXY_LOWER_PPM_BOUNDS

// -------------------- Variables --------------------
// For readouts when disconnected
unsigned long lastDisplayRequest = 0;
unsigned long displayWaitMarker = 0;

// For Wifi
int status = WL_IDLE_STATUS;
WiFiServer server(80);

// For 7 segment displays
Adafruit_7segment tempDisplay = Adafruit_7segment();
Adafruit_7segment oxyDisplay = Adafruit_7segment();
Adafruit_7segment waterDisplay = Adafruit_7segment();

// Smoothing
unsigned long measureWaitMarker;
double oxySmoothArray[SMOOTH_NUM];
double waterSmoothArray[SMOOTH_NUM];
double oxySmoothSum = 0;
double waterSmoothSum = 0;

// For Cache System
unsigned long cacheWaitMarker = 0;
String cache[CACHE_MAX];
int cacheBegin = 0;
int cacheEnd = 0;
int newCacheBegin = 0;
// String newCache = "";
// String oldCache = "";

// -------------------- Utilities --------------------
// ---------- Smoothing ----------
void addSmooth(double smoothArray[], uint16_t smoothNum, double val, double& sum) {
  sum -= smoothArray[0];
  sum += val;
  for (int i = 0; i < smoothNum - 1; ++i) {
    smoothArray[i] = smoothArray[i + 1];
  }
  smoothArray[smoothNum - 1] = val;
}
double getSmooth(double sum, uint16_t smoothNum) {
  return sum / smoothNum;
}
// ---------- Text Parsing ----------
String readFromUntil(const String& text, const String& flagStart, const String& flagEnd) {
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
bool stringContains(const String& text, const String& substring) {
  for (int i = 0; i < text.length() - substring.length(); ++i) {
    if (text.substring(i, i + substring.length()) == substring) {
      return true;
    }
  }
  return false;
}
// ---------- Sensor Calculations ----------
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
  return ((((val * VOLT_REF / 1023.0 / SENSE_RESISTANCE * 1000.0) - OXY_LOWER_CURRENT_BOUNDS) / OXY_CURRENT_RANGE)
               * OXY_PPM_RANGE)
              + OXY_LOWER_PPM_BOUNDS;
}

// -------------------- Helper Functions --------------------
// ---------- For Wifi Serial Logging ----------
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
// ---------- For Readout Displays ----------
void sevenSegPrint(Adafruit_7segment& display, const String& printMssg) {
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
void printChars(Adafruit_7segment& display, const String& printMssg) {
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
    double oxyVal = getSmooth(oxySmoothSum, SMOOTH_NUM);
    double oxyCurrent = oxyVal * 5.0 / 1023.0 / SENSE_RESISTANCE * 1000.0;
    if (oxyCurrent < OXY_LOWER_CURRENT_BOUNDS) {
      printChars(oxyDisplay, OFFSCALE_LOW_DISPLAY);
    } else if (oxyCurrent > OXY_UPPER_CURRENT_BOUNDS) {
      printChars(oxyDisplay, OFFSCALE_HIGH_DISPLAY);
    } else {
      oxyDisplay.print(calcOxy(getSmooth(oxySmoothSum, SMOOTH_NUM)));
      oxyDisplay.writeDisplay();
    }

    double waterVal = getSmooth(waterSmoothSum, SMOOTH_NUM);
    double waterCurrent = waterVal * 5.0 / 1023.0 / SENSE_RESISTANCE * 1000.0;
    if (waterCurrent < WATER_LOWER_CURRENT_BOUNDS) {
      printChars(waterDisplay, OFFSCALE_LOW_DISPLAY);
    } else if (waterCurrent > WATER_UPPER_CURRENT_BOUNDS) {
      printChars(waterDisplay, OFFSCALE_HIGH_DISPLAY);
    } else {
      waterDisplay.print(calcWater(getSmooth(waterSmoothSum, SMOOTH_NUM)));
      waterDisplay.writeDisplay();
    }
}
// ---------- For Sensor Measurements ----------
void takeMeasurements() {
  // Taking Measurements
  unsigned long oxySum = 0;
  unsigned long waterSum = 0;
  for (int i = 0; i < SMOOTH_CHUNK_SIZE; ++i) {
    oxySum += analogRead(OXY_PIN);
    waterSum += analogRead(WATER_PIN);
    delayMicroseconds(150);
  }
  double oxyAvrg = static_cast<double>(oxySum) / SMOOTH_CHUNK_SIZE;
  double waterAvrg = static_cast<double>(waterSum) / SMOOTH_CHUNK_SIZE;
  addSmooth(oxySmoothArray, SMOOTH_NUM, oxyAvrg, oxySmoothSum);
  addSmooth(waterSmoothArray, SMOOTH_NUM, waterAvrg, waterSmoothSum);
}

// -------------------- Arduino Executing Functions --------------------
void setup() {
  // Initialize Serial
  Serial.begin(9600);

  // Initialize Segment Displays with I2C addresses
  tempDisplay.begin(TEMP_DISPLAY_ADDRESS);
  oxyDisplay.begin(OXY_DISPLAY_ADDRESS);
  waterDisplay.begin(WATER_DISPLAY_ADDRESS);

  // Set up smoothing
  for (uint16_t i = 0; i < SMOOTH_NUM; ++i) {
    unsigned long oxySum = 0;
    unsigned long waterSum = 0;
    for (int i = 0; i < SMOOTH_CHUNK_SIZE; ++i) {
      oxySum += analogRead(OXY_PIN);
      waterSum += analogRead(WATER_PIN);
      delayMicroseconds(SAMPLE_RATE_DELAY);
    }
    double oxyAvrg = static_cast<double>(oxySum) / SMOOTH_CHUNK_SIZE;
    double waterAvrg = static_cast<double>(waterSum) / SMOOTH_CHUNK_SIZE;
    oxySmoothArray[i] = oxyAvrg;
    oxySmoothSum += oxyAvrg;
    waterSmoothArray[i] = waterAvrg;
    waterSmoothSum += waterAvrg;
  }

  // ----- Wifi Setup -----
  // check for the WiFi module:
  if (WiFi.status() == WL_NO_MODULE) {
    Serial.println("Communication with WiFi module failed!");
    // don't continue
    while (true);
  }
  String fv = WiFi.firmwareVersion();
  if (fv < WIFI_FIRMWARE_LATEST_VERSION) {
    Serial.println("Please upgrade the firmware");
  }
  // attempt to connect to WiFi network:
  while (status != WL_CONNECTED) {
    Serial.print("Attempting to connect to Network named: ");
    Serial.print(NETWORK_SSID);  // print the network name (SSID);
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
        // Taking Measurements
        takeMeasurements();
        measureWaitMarker += MEASUREMENT_DELAY;
      }
      // Readouts while waiting
      if (millis() >= displayWaitMarker) {
        displayWhileDisconnected();
        displayWaitMarker += DISPLAY_REFRESH_RATE;
      }
    }
  }
  server.begin(); // start the web server on port 80
  printWifiStatus(); // you're connected now, so print out the status

  // Initialize timing markers for measurement & cache cycle timing
  // measureWaitMarker = millis();
  cacheWaitMarker = millis();
}

void loop() {
  WiFiClient client = server.available();  // listen for incoming clients

  // ----- Handle Client -----
  if (client) {                    // if you get a client,
    bool shouldRespond = false;
    String currentLine = "";       // make a String to hold incoming data from the client
    while (client.connected()) {   // loop while the client's connected
      if (client.available()) {    // if there's bytes to read from the client,
        char c = client.read();    // read a byte, then
        if (c == '\n') {           // if the byte is a newline character
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
              msg += String{millis()};
              msg += END_FLAG;
              client.print(msg);
              // msg += newCache + oldCache; // want the newest data first
              // Serial.println("msg: " + msg);


              // client.print(newCache);
              // client.print(oldCache);
              // Serial.println("newCache: " + newCache);
              // Serial.println("oldCache: " + oldCache);
              // oldCache = newCache + oldCache;
              // if (oldCache.length() > MAX_CACHE_CHARS) {
              //   Serial.println("trimming old");
              //   oldCache.remove(MAX_CACHE_CHARS);
              // }
              // // when removing chars, we might lose precision or data, but we shouldn't start giving innacurate data
              // newCacheBegin = cacheEnd;


              if (cacheBegin != cacheEnd) {
                int i = cacheEnd - 1;
                while (true) {
                  client.print(cache[i]);
                  Serial.print(cache[i]);
                  if (i == cacheBegin) break;
                  i = (i - 1 + CACHE_MAX) % CACHE_MAX;  // decrement with wrap-around
                }
                newCacheBegin = cacheEnd;
              }
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
              // oldCache = "";
              cacheBegin = newCacheBegin;
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

  // ----- Adding to Cache -----
  if (millis() >= cacheWaitMarker) {
    String newCacheLog = "";
    newCacheLog += CACHE_LOG_FLAG;
    newCacheLog += CACHE_TIME_FLAG;
    newCacheLog += String{millis()};
    newCacheLog += END_FLAG;
    newCacheLog += OXY_FLAG;
    double oxy = getSmooth(oxySmoothSum, SMOOTH_NUM);  // * REFERENCE_VAL / analogRead(VOLT_REF_PIN);
    newCacheLog += String{oxy};
    newCacheLog += END_FLAG;
    newCacheLog += WATER_FLAG;
    double water = getSmooth(waterSmoothSum, SMOOTH_NUM);  // * REFERENCE_VAL / analogRead(VOLT_REF_PIN);
    newCacheLog += String{water};
    newCacheLog += END_FLAG;
    // newCache = newCacheLog + newCache;
    // if (newCache.length() > MAX_CACHE_CHARS - oldCache.length()) {
    //   newCache.remove(MAX_CACHE_CHARS - oldCache.length());
    //   Serial.println("trimming");
    //   // when removing chars, we might lose precision or data, but we shouldn't start giving innacurate data
    // }
    cache[cacheEnd] = newCacheLog;
    if (++cacheEnd >= CACHE_MAX) {
      cacheEnd = 0;
    }
    if (cacheEnd == cacheBegin) {
      for (int i = 0; i < CACHE_MAX / 2; ++i) {
        int readIndex = (cacheBegin + i * 2 + 1) % CACHE_MAX;
        int writeIndex = cacheBegin + i;
        cache[writeIndex] = cache[readIndex];
      }
      cacheEnd = (cacheBegin + CACHE_MAX / 2) % CACHE_MAX;
    }
    cacheWaitMarker += CACHE_CYCLE_DELAY;
    if (cacheBegin != cacheEnd) {
      int i = cacheEnd - 1;
      while (true) {
        Serial.print(cache[i]);
        Serial.print(" ");
        if (i == cacheBegin) break;
        i = (i - 1 + CACHE_MAX) % CACHE_MAX;  // decrement with wrap-around
      }
      Serial.println("\n");
    }
  }

  // ----- Analog Reading and Smoothing -----
  if (millis() >= measureWaitMarker) {  // wait for controlling the sensor read timing
    // Taking Measurements
    takeMeasurements();
    measureWaitMarker += MEASUREMENT_DELAY;
  }

  // ----- Readouts upon disconnect -----
  if (millis() - lastDisplayRequest >= DISPLAY_REQUEST_WAIT && millis() >= displayWaitMarker) {
    displayWaitMarker = millis() + DISPLAY_REFRESH_RATE; // Not doing the more precise cycling timer here
    displayWhileDisconnected();
  }
}
