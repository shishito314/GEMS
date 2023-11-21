// Basic bluetooth test sketch. HC-06_01_9600
// HC-06 ZS-040 
// 
// 
//  Uses hardware serial to talk to the host computer and software serial for communication with the bluetooth module
//
//  Pins
//  BT VCC to Arduino 5V out. 
//  BT GND to GND
//  BT RX to Arduino pin 3 (through a voltage divider)
//  BT TX to Arduino pin 2 (no need voltage divider)
//
//  When a command is entered in the serial monitor on the computer 
//  the Arduino will relay it to the bluetooth module and display the result.
//
//  These HC-06 modules require capital letters and no line ending
//

#include <SoftwareSerial.h>
#include "max6675.h"
SoftwareSerial BTSerial(2, 3); // RX | TX

int thermoDO = 7;//12;
int thermoCS = 6;//11;
int thermoCLK = 5;//10;

//raw data stored as past 10 data points
float rawTemps[10];
//moving average of 4 points
float smoothTemps[10];

MAX6675 thermocouple(thermoCLK, thermoCS, thermoDO);

float count = 0.0;

void setup() 
{
    Serial.begin(9600);
    Serial.println("Arduino with HC-06 is ready");

    // HC-06 default baud rate is 9600
    BTSerial.begin(9600);  
    Serial.println("BTserial started at 9600");

    Serial.println("Start temperature recording");
    // wait for MAX chip to stabilize
    delay(500);

    for(int i = 0; i < 10; i++){
      rawTemps[i] = thermocouple.readCelsius();
    }
    for(int i = 0; i < 10; i++){
      smoothTemps[i] = thermocouple.readCelsius();
    }
}

void loop()
{

  // Keep reading from HC-06 and send to Arduino Serial Monitor
  if (BTSerial.available()) {
    while(BTSerial.available()) { BTSerial.read(); }
    
    //Serial.write(BTSerial.read());
    //Serial.print("\n");
    shiftArr(rawTemps, sizeof(rawTemps)/sizeof(rawTemps[0]));
    rawTemps[9] = thermocouple.readCelsius();
    //Add most recent measurement to smooth
    shiftArr(smoothTemps, sizeof(smoothTemps)/sizeof(smoothTemps[0]));
    smoothTemps[9] = avgArr(rawTemps, sizeof(rawTemps)/sizeof(rawTemps[0]));

    BTSerial.print(smoothTemps[9]);
  }
  
  // Keep reading from Arduino Serial Monitor and send to HC-06
  //if (Serial.available()) {
  //  BTSerial.write(Serial.read());
  //}
}


void shiftArr(float arr[], int sizeArr){
  for(int i = 0; i < sizeArr - 1; i++){
    arr[i] = arr[i+1];
  }
}

float avgArr(float arr[], int sizeArr){
  float avg = 0;
  for(int i = 0; i < sizeArr; i++){
    avg += arr[i];
  }
  if(sizeArr != 0){
    avg = avg/sizeArr;
    return avg;
  }
  else{
    return 0;
  }
}
