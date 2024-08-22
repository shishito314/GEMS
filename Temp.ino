// For Wifi
#include <SPI.h>
#include <WiFiNINA.h>
// For Thermocouple
#include "max6675.h"

// -------------------- Constants (Must Match Python) --------------------
// For HTTP Communication
// NOTE: Make sure none of these flags are contained within the other flags, as it will mess up text parsing
constexpr char* TEMP_FLAG = "Temp:";  //                                                                        MUST MATCH PYTHON

// For Cache System
constexpr char* CACHE_LOG_FLAG = "Log:"; //                                                                     MUST MATCH PYTHON
constexpr char* REQUEST_RECIEVED_FLAG = "Received"; //                                                          MUST MATCH PYTHON
constexpr char* DATA_TRANSFER_SUCCESS_FLAG = "Success"; //                                                      MUST MATCH PYTHON
constexpr char* CACHE_REQUEST_FLAG = "Log_";
constexpr char* CACHE_TIME_FLAG = "Time:"; //                                                                   MUST MATCH PYTHON

constexpr char* END_FLAG = "End"; //                                                                            MUST MATCH PYTHON

// -------------------- Other Constants --------------------
// ---------- May Be Changed ----------
constexpr char* NETWORK_SSID = "ChiangGroupWifi";  // your network SSID (name)
constexpr char* NETWORK_PASS = "EVs4ALL!";  // your network password (using WPA)

// For Digital Filter (Moving Average)
// Using a simpler moving average than the oxygen or water sensors, since the maximum sampling rate slower anyway
constexpr uint8_t MEASUREMENT_DELAY = 250; // max66775 maximum sampling rate is listed at ~4Hz (4.3)
constexpr uint16_t SMOOTH_NUM = 20;

// Thermocouple module pins
constexpr uint8_t THERMO_CLK = 10;
constexpr uint8_t THERMO_CS = 11;
constexpr uint8_t THERMO_DO = 12;

// For Cache System
constexpr uint16_t CACHE_CYCLE_DELAY = 5000;
constexpr uint16_t MAX_CACHE_CHARS = 4500;

// ---------- Should Not Change ----------
// HTTP Communcation Flags (For internal use)
const String HTTP_CACHE_REQUEST_FLAG = String{"GET /"} + CACHE_REQUEST_FLAG;

// -------------------- Variables --------------------
int status = WL_IDLE_STATUS;
WiFiServer server(80);

MAX6675 thermocouple{THERMO_CLK, THERMO_CS, THERMO_DO};

// Smoothing
unsigned long measureWaitMarker;
double tempSmoothArray[SMOOTH_NUM];
double tempSmoothSum = 0;

// For Cache System
uint32_t cacheWaitMarker = 0;
String newCache = "";
String oldCache = "";

// -------------------- Utilities --------------------
// ---------- Smoothing ----------
void addSmooth(double* smoothArray, uint16_t smoothNum, double val, double& sum) {
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

// ---------- For Sensor Measurements ----------
void takeMeasurements() {
  addSmooth(tempSmoothArray, SMOOTH_NUM, thermocouple.readCelsius(), tempSmoothSum);
}

// -------------------- Arduino Executing Functions --------------------
void setup() {
  // Initialize Serial
  Serial.begin(9600);

  // Set up smoothing
  for (uint16_t i = 0; i < SMOOTH_NUM; ++i) {
    double temp = thermocouple.readCelsius();
    tempSmoothArray[i] = temp;
    tempSmoothSum += temp;
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
    // ----- Loop while waiting -----
    while (millis() < startTime + 10000) {
      // Starts looping for live readouts before connected
      if (millis() >= measureWaitMarker) {  // wait for controlling the sensor read timing
        // Taking Measurements
        takeMeasurements();
        measureWaitMarker += MEASUREMENT_DELAY;
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
              msg += newCache + oldCache; // want the newest data first
              client.print(msg);
              // Serial.println(msg);
              oldCache = newCache + oldCache;
              if (oldCache.length() > MAX_CACHE_CHARS) {
                oldCache.remove(MAX_CACHE_CHARS);
              }
              // when removing chars, we might lose precision or data, but we shouldn't start giving innacurate data
              newCache = "";
            }
            // ----- End Sending Response -----

            // The HTTP response ends with another blank line:
            client.println();
            // break out of the while loop:
            break;
          } else {
            // ----- Reading Request -----
            if (stringContains(currentLine, DATA_TRANSFER_SUCCESS_FLAG)) {
              oldCache = "";
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

  // ----- Adding to Cache -----
  if (millis() > cacheWaitMarker) {
    String newCacheLog = "";
    newCacheLog += CACHE_LOG_FLAG;
    newCacheLog += CACHE_TIME_FLAG;
    newCacheLog += String{millis()};
    newCacheLog += END_FLAG;
    newCacheLog += TEMP_FLAG;
    double temp = getSmooth(tempSmoothSum, SMOOTH_NUM);
    newCacheLog += String{temp};
    newCacheLog += END_FLAG;
    newCache = newCacheLog + newCache;
    if (newCache.length() > MAX_CACHE_CHARS - oldCache.length()) {
      newCache.remove(MAX_CACHE_CHARS - oldCache.length());
      // when removing chars, we might lose precision or data, but we shouldn't start giving innacurate data
    }
    cacheWaitMarker += CACHE_CYCLE_DELAY;
  }

  // ----- Analog Reading and Smoothing -----
  if (millis() >= measureWaitMarker) {  // wait for controlling the sensor read timing
    // Taking Measurements
    takeMeasurements();
    measureWaitMarker += MEASUREMENT_DELAY;
  }
}