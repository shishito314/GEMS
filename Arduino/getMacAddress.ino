#include <SPI.h>
#include <WiFiNINA.h>

char ssid[] = [Insert Network Name Here];     // the name of your network
char pass[] = [Insert Network Password Here];
int status = WL_IDLE_STATUS;     // the WiFi radio's status

byte mac[6];                     // the MAC address of your WiFi Module


void setup()
{
 Serial.begin(9600);

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
    Serial.println(ssid);  // print the network name (SSID);

    // Connect to WPA/WPA2 network. Change this line if using open or WEP network:
    status = WiFi.begin(ssid, pass);
    // wait 10 seconds for connection:
    delay(10000);
  }
  // if you are connected, print your MAC address:
  WiFi.macAddress(mac);
  Serial.print("MAC: ");
  printHex(mac[5]);
  Serial.print(":");
  printHex(mac[4]);
  Serial.print(":");
  printHex(mac[3]);
  Serial.print(":");
  printHex(mac[2]);
  Serial.print(":");
  printHex(mac[1]);
  Serial.print(":");
  printHex(mac[0]);
  Serial.println();
  // print network
  Serial.print("SSID: ");
  Serial.println(WiFi.SSID());

  // print your board's IP address:
  IPAddress ip = WiFi.localIP();
  Serial.print("IP Address: ");
  Serial.println(ip);
}

void printHex(byte data) {
  if (data < 10) {
    Serial.print(0);
  }
  Serial.print(data, HEX);
}

void loop () {}
