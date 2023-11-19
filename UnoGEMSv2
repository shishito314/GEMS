// Basic Bluetooth sketch HC-05_AT_MODE_01
// Connect the HC-05 module and communicate using the serial monitor
//
// The HC-05 defaults to commincation mode when first powered on you will need to manually enter AT mode
// The default baud rate for AT mode is 38400
// See www.martyncurrey.com for details
//

#include <Wire.h> // Enable this line if using Arduino Uno, Mega, etc.
#include <Adafruit_GFX.h>
#include "Adafruit_LEDBackpack.h"
#include <SoftwareSerial.h>

const float WATER_LOWER_CURRENT_BOUNDS = 4;
const float WATER_UPPER_CURRENT_BOUNDS = 20;
const int WATER_LOWER_DEW_BOUNDS = -100;
const int WATER_UPPER_DEW_BOUNDS = 20;

const float OXY_LOWER_CURRENT_BOUNDS = 4;
const float OXY_UPPER_CURRENT_BOUNDS = 20;
const float OXY_LOWER_PPM_BOUNDS = 0;
const float OXY_UPPER_PPM_BOUNDS = 100;

const int WATER_PIN = 2;
const int OXY_PIN = 1;
const int AREF_PIN = 0;

const int SENSE_RESISTANCE = 220;
const float AREF_VOLTAGE = 3.3f;

Adafruit_7segment matrixTemp = Adafruit_7segment();
Adafruit_7segment matrixWater = Adafruit_7segment();
bool showWater = true;
 
SoftwareSerial BTserial(2, 3); // RX | TX
// Connect the HC-05 TX to Arduino pin 2 RX. 
// Connect the HC-05 RX to Arduino pin 3 TX through a voltage divider.
 
void setup() 
{
    Serial.begin(9600);
    Serial.println("Arduino is ready");
    Serial.println("Remember to select Both NL & CR in the serial monitor");

    matrixTemp.begin(0x71);
    matrixWater.begin(0x70);

    // HC-05 default serial speed for AT mode is 38400
    BTserial.begin(9600);  
}
 
void loop()
{
  /*
  // Keep reading from Arduino Serial Monitor and send to HC-05
  if (Serial.available())
  {
      char c =  Serial.read();
      BTserial.write(c);  
      Serial.write(c);  
  }
  */
  
  // SENSOR READING
  measureOxy();
  measureWater();
  getTemp();
  Serial.println("");
  showWater = !showWater;

  delay(500);
    
}

void measureWater() {
  float voltRead = analogRead(WATER_PIN);
  float arefReading = analogRead(AREF_PIN);

  //Serial.println(voltRead);
  //Serial.println(voltRead * AREF_VOLTAGE / arefReading);
  float current = voltRead / SENSE_RESISTANCE * AREF_VOLTAGE / arefReading * 1000;
  //Serial.println(current);

  float dewPoint = (
      (
        (current - WATER_LOWER_CURRENT_BOUNDS) /
        (WATER_UPPER_CURRENT_BOUNDS - WATER_LOWER_CURRENT_BOUNDS)
      ) * 
      (WATER_UPPER_DEW_BOUNDS - WATER_LOWER_DEW_BOUNDS)
    ) +
      WATER_LOWER_DEW_BOUNDS;
  //Serial.println(dewPoint);

  float exponent = (13.6627 - 2720.84 / (275.38 + dewPoint));
  float ppm = pow(10, exponent);
  Serial.print("Water: ");
  Serial.print(ppm);
  Serial.print(" ");

  // TODO: Testing for Printing
  if (showWater) {
    matrixWater.print(ppm);
    matrixWater.writeDisplay();
  }
}

void measureOxy() {
  float voltRead = analogRead(OXY_PIN);
  float arefReading = analogRead(AREF_PIN);

  //Serial.println(arefReading);
  //Serial.println(voltRead);
  //Serial.println(voltRead * AREF_VOLTAGE / arefReading);
  float current = voltRead / SENSE_RESISTANCE * AREF_VOLTAGE / arefReading * 1000;
  //Serial.println(current);

  float ppm = (
      (
        (current - OXY_LOWER_CURRENT_BOUNDS) /
        (OXY_UPPER_CURRENT_BOUNDS - OXY_LOWER_CURRENT_BOUNDS)
      ) * 
      (OXY_UPPER_PPM_BOUNDS - OXY_LOWER_PPM_BOUNDS)
    ) +
      OXY_LOWER_PPM_BOUNDS;

  Serial.print("Oxygen: ");
  Serial.print(ppm);
  Serial.print(" ");

  // TODO: Testing for Printing
  if (!showWater) {
    matrixWater.print(ppm);
    matrixWater.writeDisplay();
  }
}

void getTemp() {
  String temp;
  while (BTserial.available())
  {  
      char c = BTserial.read();
      //Serial.print(c);
      temp += c;  
  }
  //Serial.println("");
  Serial.print("Temp: ");
  Serial.print(temp);
  // Serial.print(" ");
  matrixTemp.print(temp.toFloat());
  matrixTemp.writeDisplay();
}
