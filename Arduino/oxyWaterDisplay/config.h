#pragma once
// -------------------- Constants (Must Match Python) --------------------
// NOTE: Using #define instead of const or constexpr to save memory (sounds dumb but makes a difference)

// For HTTP Communication
// NOTE: Make sure none of these flags are contained within the other flags, as it will mess up text parsing
#define TEMP_FLAG "T<"  //                                                                       MUST MATCH PYTHON
#define OXY_FLAG "O<"   //                                                                       MUST MATCH PYTHON
#define WATER_FLAG "W<" //                                                                       MUST MATCH PYTHON

// For Cache System
#define CACHE_LOG_FLAG "L:"                  //                                                  MUST MATCH PYTHON
#define REQUEST_RECIEVED_FLAG "Received"     //                                                  MUST MATCH PYTHON
#define DATA_TRANSFER_SUCCESS_FLAG "Success" //                                                  MUST MATCH PYTHON
#define CACHE_REQUEST_FLAG "Log_"
#define CACHE_TIME_FLAG "Time<" //                                                               MUST MATCH PYTHON

// Misc. Communication Flags
#define DISPLAY_FLAG "Display_"       //                                                         MUST MATCH PYTHON
#define DISPLAY_ERROR_MESSAGE "Error" //                                                         MUST MATCH PYTHON

#define END_FLAG ">" //                                                                          MUST MATCH PYTHON

// -------------------- Other Constants --------------------
// ---------- May Be Changed ----------
#define NETWORK_SSID "YourNetworkName"      // your network SSID (name)
#define NETWORK_PASS "YourNetworkPassword!" // your network password (using WPA)

// For Readouts On Disconnect
#define DISPLAY_REQUEST_WAIT 65000 // how long to wait for the HTTP request before changing to on-arduino calculation + readout
#define DISPLAY_REFRESH_RATE 20000

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
#define VOLT_REF 4.5

// Analog Reading Pins
#define OXY_PIN A0   // The analog pin connected to the Oxygen Sensor
#define WATER_PIN A5 // The same, for the water sensor

// For Digital Filter (Moving Average)
#define MEASUREMENT_DELAY 0 // as quick a sample rate as possible
#define SMOOTH_NUM 20
#define SMOOTH_CHUNK_SIZE 125

// For Cache System
#define CACHE_CYCLE_DELAY 30000
#define CACHE_MAX 50 // Should not be less than 4
#define MAX_CACHE_ENTRY_SIZE 65

#define OFFSCALE_HIGH_DISPLAY "HI" // For displays when disconnected
#define OFFSCALE_LOW_DISPLAY "LO"  // For displays when disconnected

#define TEMP_DISPLAY_ADDRESS 0x70
#define OXY_DISPLAY_ADDRESS 0x71
#define WATER_DISPLAY_ADDRESS 0x72

// ---------- Should Not Change ----------
// HTTP Communcation Flags (For internal use)
const String HTTP_DISPLAY_FLAG = String{"GET /"} + DISPLAY_FLAG;
const String HTTP_CACHE_REQUEST_FLAG = String{"GET /"} + CACHE_REQUEST_FLAG;

// For Calculating Sensor Measurement (Internal Use)
#define WATER_CURRENT_RANGE (WATER_UPPER_CURRENT_BOUNDS - WATER_LOWER_CURRENT_BOUNDS)
#define WATER_DEW_RANGE (WATER_UPPER_DEW_BOUNDS - WATER_LOWER_DEW_BOUNDS)
#define OXY_CURRENT_RANGE (OXY_UPPER_CURRENT_BOUNDS - OXY_LOWER_CURRENT_BOUNDS)
#define OXY_PPM_RANGE (OXY_UPPER_PPM_BOUNDS - OXY_LOWER_PPM_BOUNDS)