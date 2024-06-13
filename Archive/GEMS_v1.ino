#include <SPI.h> // SPI communication
#include <SD.h> // SD card IO
#include <RTClib.h> // Real-time clock for data logging

void setup() {
  Serial.begin(57600); // Open serial port, for debugging
  while (! Serial); // Wait for serial port to open


  // ---Pins and reference values---

  const int arefPin = A0; // Pin for reference voltage
  const float aref = 3.3f; // Reference voltage of 3.3V
  const int O2Pin = A1; // Pin for reading voltage from O2 sensor
  const int H2OPin = A2; // Pin for reading voltage from H2O sensor
  const float senseResistance = 220.0f;
  const int chipSelect = 10; // Pin for chip select


  // ---Time steps---

  // Code will perform three actions at regular intervals:
  // Read = check the values from each sensor
  // Disp = write values to the onboard display
  // Save = save values to archive
  const unsigned long readInterval = 500; // ms
  const unsigned long dispInterval = 500;
  const unsigned long saveInterval = 5000;


  // ---Initialize variables---

  // previousXXXX = last time XXXX was performed
  const unsigned long previousRead = 0;
  const unsigned long previousDisp = 0;
  const unsigned long previousSave = 0;

  bool readNow = false;
  bool dispNow = false;
  bool saveNow = false;

  float O2current = 0.0f;
  float H2Ocurrent = 0.0f;
  float temp = 0.0f;


  // ---Initialize real-time clock---

  // Mostly copied from datalogger shield documentation
  RTC_PCF8523 rtc;
  Serial.print("Initializing RTC...");
  if (! rtc.begin()) {
    Serial.println("Couldn't find RTC");
    Serial.flush();
  }
  else {
    Serial.println("RTC found.");
  }

  if (! rtc.initialized() || rtc.lostPower()) {
    // Gets called when initializing a new device, or after a power loss.
    Serial.println("RTC time needs to be set.");
    // The following line sets the RTC to the date & time this sketch was compiled.
    rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
    // Note: allow 2 seconds after inserting battery or applying external power
    // without battery before calling adjust().
  }

  // Use the following line if an explicit date & time needs to be set.
  // Fill in fields with appropriate numbers.
  // rtc.adjust(DateTime(YYYY, M, D, H, M, S))


  // ---Initialize SD card---

  // Mostly copied from datalogger shield documentation
  Serial.print("Initializing SD card...");
  if (! SD.begin(chipSelect)) {
    Serial.println("Card failed, or not present.");
  }
  else {
    Serial.println("Card initialized.");
  }

  // Columns in csv for datalogging
  const char sdHeader = "Date,Time,O2 ppm,H2O ppm,Temp C";
}

void timer() {
  // Keeps track of time elapsed since system was powered on
  // Compares against the desired intervals for each action
  // Sets flags readNow, dispNow, saveNow when actions are due
  // These flags trigger subroutines downstream

  unsigned long currentMillis = millis(); // Number of milliseconds since bootup
  // Beware of integer overflow, it will happen every 49.7 days of uptime and needs to be handled
  
  // Initialize flags to false
  readNow = false;
  dispNow = false;
  saveNow = false;

  if (currentMillis >= previousRead + readInterval) {
    readNow = true;
    previousRead += readInterval;
  }
  if (currentMillis >= previousDisp + dispInterval) {
    dispNow = true;
    previousDisp += dispInterval;
  }
  if (currentMillis >= previousSave + saveInterval) {
    saveNow = true;
    previousSave += saveInterval;
  }
} 

float loopCurrent(int inputPin) {
  // Input: pin to read voltage from, e.g. A1, A2; value should be either O2Pin or H2OPin
  // Output: current across that pin's sense resistor
  int analogReading = analogRead(inputPin);
  int arefReading = analogRead(arefPin);

  // Compares voltage of pin being read to reference pin
  float loopCurrent = aref / senseResistance * analogReading / arefReading;
  return loopCurrent;
}

void saveToSD() {
  // Save current values to the SD card
  // Would like to create a new file for each date so that they're manageable in size

  // Calculate current date/time
  DateTime now = rtc.now();

  // Store date as a string
  char dateBuffer[9];
  sprintf(dateBuffer, "%04u%02u%02u", now.year(), now.month(), now.day());
  char date[] = dateBuffer;

  // Create a csv filename from the date
  char filename[13];
  sprintf(filename, "%s.csv", dateBuffer);
  Serial.println(filename); // Print filename for debugging
  
  // Store time as a string
  char timeBuffer[7];
  sprintf(timeBuffer, "%02u%02u%02u", now.hour(), now.minute(), now.second());
  char time[] = timeBuffer;

  if (! SD.exists(filename)) {
    // Only open a new file if it doesn't exist
    logFile = SD.open(filename, FILE_WRITE);
    // Create the header row for a new file
    logFile.println(sdHeader);
  }

  // If a file is available, write to it
  if (logFile) {
    logFile.println(dataString);
    logFile.close();
    // Print to serial port, for debugging
    Serial.println(dataString);
  }
  // If the file isn't open, throw an error
  else {
    Serial.println("Error opening log file.");
  }

}

void loop() {
  timer();
  O2current = loopCurrent(O2Pin);
  H2Ocurrent = loopCurrent(H2OPin);
  // SUBROUTINES TO WRITE:
  // average arrays of recent values to smooth data
  // ppm from current values (if readNow)
  // bluetooth input from thermometer (if readNow)
  // set flags for LO or HI limits
  // disp values (if dispNow)
  // save to SD: time, O2 ppm/flag, H2O ppm/flag, temp (if saveNow)
}
