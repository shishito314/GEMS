// For Wifi
#include <SPI.h>
#include <WiFiNINA.h>

// Thermocouple
#include <max6675.h>

#include "config.h"
#include "circularCache.h"
#include "smoothing.h"

// -------------------- Variables --------------------
// For Wifi
int status{ WL_IDLE_STATUS };
WiFiServer server{ 80 };

bool reconnecting = false;
unsigned long reconnectStart = 0;

// Thermocouple
MAX6675 thermocouple{ THERMO_CLK, THERMO_CS, THERMO_DO };

// Smoothing
unsigned long measureWaitMarker;
Smoothing tempSmooth{};

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
void takeMeasurements() {
  // Taking Measurements
  double temp = thermocouple.readCelsius();
  tempSmooth.addValue(temp);
}
void initSmoothing() {
  for (uint16_t i = 0; i < SMOOTH_NUM; ++i) {
    double temp = thermocouple.readCelsius();
    tempSmooth.smoothArray[i] = temp;
    tempSmooth.smoothSum += temp;
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
    // ----- Loop while waiting -----
    while (millis() < startTime + 10000) {
      // Starts looping for live readouts before connected
      if (millis() >= measureWaitMarker) {  // wait for controlling the sensor read timing
        takeMeasurements();
        measureWaitMarker += MEASUREMENT_DELAY;
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
    newCacheLog += TEMP_FLAG;
    double temp = tempSmooth.getValue();
    newCacheLog += String{ temp };
    newCacheLog += END_FLAG;
    cache.add(newCacheLog);
    cacheWaitMarker += CACHE_CYCLE_DELAY;
  }

  // ----- Analog Reading and Smoothing -----
  if (millis() >= measureWaitMarker) {  // wait for controlling the sensor read timing
    takeMeasurements();
    measureWaitMarker += MEASUREMENT_DELAY;
  }
}