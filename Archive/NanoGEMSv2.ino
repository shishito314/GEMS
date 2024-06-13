//In-Glovebox temperature measurement and bluetooth output signal
//Includes built in smoothing function (moving average)
//Author: Matthew Ko 4/27/23

//module for converting thermocouple to arduino
#include "max6675.h"
#include <SoftwareSerial.h>
//#include <curveFitting.h>

//Pins that the MAX6675 module is connected to: thermoDO is SO (serial output), thermoCS is CS, thermoCLK is SCK (clock)
int thermoDO = 7;//12;
int thermoCS = 6;//11;
int thermoCLK = 5;//10;

//raw data stored as past 10 data points
double rawTemps[10];
//moving average of 4 points
double smoothTemps[10];


//void shiftArr(double []);
//double avgArr(double []);3
//double slopeArr(double []);

int counter = 0;

MAX6675 thermocouple(thermoCLK, thermoCS, thermoDO);

SoftwareSerial BTserial(2, 3); // RX | TX

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
  BTserial.begin(9600);  

  Serial.println("Start temperature recording");
  // wait for MAX chip to stabilize
  delay(500);
  pinMode(2, OUTPUT);
  pinMode(3, OUTPUT);

  pinMode(4, OUTPUT);
  pinMode(5, OUTPUT);
  pinMode(6, OUTPUT);
  pinMode(7, OUTPUT);
  pinMode(8, OUTPUT);
  pinMode(9, OUTPUT);

  counter = 0;
}

void loop() {
  // put your main code here, to run repeatedly:
  //If no data yet, set all data to be first measurement
  if(counter == 0){
    for(int i = 0; i < 10; i++){
      rawTemps[i] = thermocouple.readCelsius();
    }
    for(int i = 0; i < 10; i++){
      smoothTemps[i] = thermocouple.readCelsius();
    }
  }
  else{
    //Add most recent measurement to raw. sizeof gives size in bits, so divide by size of one element
    shiftArr(rawTemps, sizeof(rawTemps)/sizeof(rawTemps[0]));
    rawTemps[9] = thermocouple.readCelsius();
    //Add most recent measurement to smooth
    shiftArr(smoothTemps, sizeof(smoothTemps)/sizeof(smoothTemps[0]));
    smoothTemps[9] = avgArr(rawTemps, sizeof(rawTemps)/sizeof(rawTemps[0]));
  }


  //Serial.println(smoothTemps[9]); 
  BTserial.print(smoothTemps[9]);


    // Keep reading from HC-05 and send to Arduino Serial Monitor
    if (BTserial.available())
    {  
        char c = BTserial.read();
        Serial.write(c);
    }
 
    // Keep reading from Arduino Serial Monitor and send to HC-05
    if (Serial.available())
    {
        char c =  Serial.read();
        BTserial.write(c);  
        Serial.write(c);  
    }


  //Serial.print(",");
  //Serial.print(rawTemps[9]);
  //Serial.print(",");
  //Serial.print(heatRate > threshHRate);
  //Serial.print(",");
  //Serial.print(smoothTemps[9] > threshC);
  //Serial.print(",");
  //Serial.println(heating);
  // For the MAX6675 to update, you must delay AT LEAST 250ms between reads!
  delay(500);
  counter++;
}

void shiftArr(double arr[], int sizeArr){
  for(int i = 0; i < sizeArr - 1; i++){
    arr[i] = arr[i+1];
  }
}

double avgArr(double arr[], int sizeArr){
  double avg = 0;
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
