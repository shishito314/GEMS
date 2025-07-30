#pragma once
// -------------------- Constants (Must Match Python) --------------------
// For HTTP Communication
// NOTE: Make sure none of these flags are contained within the other flags, as it will mess up text parsing
#define TEMP_FLAG "T<"  //                                                                       MUST MATCH PYTHON

// For Cache System
#define CACHE_LOG_FLAG "L:"                   //                                                  MUST MATCH PYTHON
#define REQUEST_RECIEVED_FLAG "Received"      //                                                  MUST MATCH PYTHON
#define DATA_TRANSFER_SUCCESS_FLAG "Success"  //                                                  MUST MATCH PYTHON
#define CACHE_REQUEST_FLAG "Log_"
#define CACHE_TIME_FLAG "Time<"  //                                                               MUST MATCH PYTHON

#define END_FLAG ">"  //                                                                          MUST MATCH PYTHON

// -------------------- Other Constants --------------------
// ---------- May Be Changed ----------
#define NETWORK_SSID "ChiangGroupWifi"  // your network SSID (name)
#define NETWORK_PASS "EVs4ALL!"         // your network password (using WPA)

// Thermocouple module pins
#define THERMO_CLK 10
#define THERMO_CS 11
#define THERMO_DO 12

// For Digital Filter (Moving Average)
#define MEASUREMENT_DELAY 250  // max66775 maximum sampling rate is listed at ~4Hz (4.3)
#define SMOOTH_NUM 20
// #define SMOOTH_CHUNK_SIZE 125

// For Cache System
#define CACHE_CYCLE_DELAY 5000
#define CACHE_MAX 50  // Should not be less than 4
#define MAX_CACHE_ENTRY_SIZE 65

// ---------- Should Not Change ----------
// HTTP Communcation Flags (For internal use)
const String HTTP_CACHE_REQUEST_FLAG = String{ "GET /" } + CACHE_REQUEST_FLAG;