# GEMS - Glovebox Environmental Monitoring System

## Table of Contents

- [Overview](#overview)
- [Instructions For Use](#instructions-for-use)
  - [Setup](#setup)
  - [Binding Arduino MAC Addresses](#binding-arduino-mac-addresses)
  - [Changing Display I2C Addresses](#changing-display-i2c-addresses)
  - [Python Configuration](#python-configuration)
  - [Adding Sensors](#adding-sensors)
  - [Changing Program Constants and Parameters](#changing-program-constants-and-parameters)
- [How GEMS works](#how-gems-works)
  - [Hardware](#hardware)
    - [Bill Of Materials](#bill-of-materials)
    - [Wifi Communications](#wifi-communications)
    - [Sensor Measurement](#sensor-measurement)
  - [Software](#software)
    - [Python Overview](#python-overview)
    - [Arduino Code Overview](#arduino-code-overview)
    - [Technical Details](#technical-details)
      - [Wifi & Caching](#wifi--caching)
      - [Smoothing](#smoothing)
      - [Behavior on Disconnect](#behavior-on-disconnect)
- [Known Issues and Limitations](#known-issues-and-limitations)
- [Links](#links)

### Overview

Here's the basic idea of the GEMS system in it's current implementation:

There are two arduino boards, one inside and one outside the glovebox. The one inside is connected to a temperature sensor. The one outside is connected to an oxygen sensor, a water/humidity sensor, and three displays (one to display each sensor measurement).

When the loop.py program is run on a computer connected to the GEMS router network, it will periodically send HTTP requests to the arduinos, which are effectively hosting servers. When it sends the request, the arduino will respond with the current sensor measurement (in the form of an HTML webpage). When it gets the measurements, the computer will log them in a file.

Then, with the current measurements, the computer will decide what should be displayed. With another HTTP request, it will send that information to the arduino with the displays, which will update the displays accordingly. Then, on the next cycle, the computer will run that entire process again, and so on.

## Instructions For Use

### Setup

Here's the full setup you need for GEMS to work:

- Computer
  - Wifi adapter plugged in
  - Connected to router network
  - Python 3 installed
  - Python programs downloaded in the same directory as the log files will be stored
  - GEMS Configuration file setup correctly
  - Loop.py running
- Sensor PCB
  - Displays soldered together (Adafruit guide [here](https://learn.adafruit.com/adafruit-7-segment-led-featherwings/overview))
  - Displays soldered with correct I2C addresses (explanation [here](#changing-display-i2c-addresses))
  - Displays plugged into header pins on PCB
  - Sensor leads connected to screw terminals
  - Arduino connected to header pins on PCB
  - Barrel power jack connected to 24V Wall adapter (connected to wall power)
- Arduinos
  - Network information input correctly
  - Correct sketch uploaded
  - Thermocouple plugged in to Temperature Arduino
  - Arduino (or PCB) plugged in and running
- Router
  - Arduino MAC addresses bound to IP addresses listed in the configuration file

### Binding Arduino MAC Adresses

1. Get the Arduino MAC address with the GetMacAddress Sketch
2. Connect to the router network and go to the configuration page at [http://tplinkwifi.net/](http://tplinkwifi.net/)
3. Sign in with password posted on the router
4. Click "DHCP" on the left
5. Click "Address Reservation"
6. Add a new line, and input the MAC Address with the desired IP Address
7. Switch to "Enable"

### Changing Display I2C Addresses

The seven segment displays communicate with the Arduino via the I2C protocol, which requires each device to have a unique address. Luckily, we can change the address from the default 0x70 by soldering on the display board.

There are 3 address jumpers on the display board (the pairs of solder pads marked A0, A1, A2). Each jumper represents a bit: 1, 2, and 4 for A0, A1, and A2 respectively. The final address is 0x70 + the sum of all the bits. For example, to get the address 0x73, you would solder together the A0 pads and A1 pads (70 + 1 + 2 = 73).

You can find the Adafruit guide on changing the I2C addresses [here](https://learn.adafruit.com/adafruit-7-segment-led-featherwings/pinouts#changing-addresses-1805676)

In the current GEMS Arduino code, the displays are set up as follows:

- Temperature display → 0x70 (no jumpers)
- Oxygen display → 0x71 (A0 soldered)
- Water display → 0x72 (A1 soldered)

### Python Configuration

To configure the software for certain gloveboxes, arduinos, and sensors, use the config.txt file.
Here's the format for a config file:

```
Glovebox: [Name]
Arduino: IP: [IP Adress] Display: [True/False] Sensors: [Sensor1 Sensor2...]
Arduino: IP: [IP Adress] Display: [True/False] Sensors: [Sensor1 Sensor2...]
Glovebox: [Name]
[Arduinos...]
...
```

Here's an example of a config file following that format:

```
Glovebox: pluto
Arduino: IP: 192.168.0.110 Display: True Sensors: Oxy Water
Arduino: IP: 192.168.0.111 Display: False Sensors: Temp
Glovebox: neptune
Arduino: IP: 192.168.0.112 Display: True Sensors: Oxy
Arduino: IP: 192.168.0.113 Display: False Sensors: Temp
```

It's important to note, the colons after words are mandatory.

### Adding Sensors:

Each sensor has a class in gems.py extended from the base Sensor class. To create your own, make a class extended from the base Sensor class and define the addVal and getLog methods for your sensor. It might look something like the following:

```python
class newSensor(Sensor):
  flag = NEW_SENSOR_FLAG # Flag to be used in HTTP communications and logging
  datatype = float # The datatype of the sensor measurements (e.g. float)
  logCharLimit = 5 # The number of characters allocated to the sensor's measurement in a line of the log file

  def __init__(self):
    super().__init__()
    self.lastValue = None

  def getLog(self):
    try:
      return str(round(self.lastValue, 3))
    except:
      try:
        return self.lastValue
      except:
        return "Error"

  def getDisplay(self):
    try:
      return str(round(self.lastValue, 3))
    except:
      if (self.lastValue):
        return self.lastValue
      else:
        return DISPLAY_ERROR_MESSAGE

  def addVal(self, val):
    self.lastValue = val
```

You can also look at the sensor classes already implemented for some examples.

After making the sensor, class, add a corresponding configuration flag and sensor class to the "SENSOR_CONFIG_FLAG_TO_CLASS" dictionary in the "Set Up Class Instances From Config" section of gems.py. You'll also need to define a flag, (whatever you'd put in place of "NEW_SENSOR_FLAG" in the above example), and add that flag to the LOG_FLAGS list in the constants section of gems.py. It'll get used for parsing through log files with the data utilities.

### Changing Program Constants and Parameters

When changing constants in the programs, it is important to note that variables labeled "MUST MATCH ARDUINO" or "MUST MATCH PYTHON" must be the same in both programs. They should be at the top of gems.py or in the config.h file in the arduino sketches.

## How GEMS works

### Hardware

#### [Bill Of Materials]([https://docs.google.com/spreadsheets/d/1ikpGfJ6LjHaBAVGgCHs3OJ50SzMK_VNal6e07bsFQgU/edit?usp=sharing])

#### Wifi Communications

Required:

- Computer with python 3
- Router
- Wifi adapter
- Arduinos

The wifi adapter connects the computer to the router network, and the router network connects the computer and arduinos together. The arduinos are hosting a server, which the computer can send a request to by sending it to "http://" followed by the arduino IP address. The arduinos must have an IP address that doesn't change, so we use the MAC address binding on the router to keep the IP address constant.

#### Sensor Measurement

The oxygen and moisture sensors are 4-20 milliamp loop sensors, with a power lead (24V) and an output (goes across a resistor to GND) The sensor regulates the current on the output to be between 4 and 20 milliamps, and the current corresponds to the sensor measurement.

Since the arduinos can't measure current directly, we instead measure the voltage drop across a known resistor and calculate the current

Since it is important to know the resistance of the resistor accurately, there is a 0.1% tolerance resistor with 25ppm per degree C temperature coefficient.

There are some other pieces of hardware that address a few problems:

- Capacitor
  - There is a 10 uF capacitor running in parrallel with the resistor. It acts as a low pass filter to reduce some of the noise (15.5KHz sine wave) that had been a prior issue
- Voltage Reference
  - The built in Arduino voltage references weren't accurate enough for the desired specs, so we use an external 4.5V reference.

### Software

#### Python Overview

- [loop.py](./Python/loop.py): The update loop that sends http requests and logs data. It's an infinite loop that must be stopped by closing the python terminal.
- [gems.py](./Python/gems.py): All the architecture and setup for the GEMS system. Parses config.txt upon import.
- [data.py](./Python/data.py): Utility functions for extracting and plotting data from GEMS log files.
- [gui.py](./Python/gui.py): Runs the GEMS GUI (graphical user interface). You can use it to check up on the GEMS system and measurements.

#### Arduino Code Overview

- [oxyWaterDisplay](./Arduino/oxyWaterDisplay/): Handles sensor measurements for the oxygen and dewpoint sensors, wifi communication, and readouts.

- [temp](./Arduino/temp/): Similar to the oxyWaterDisplay sketch, but stripped down for only the temperature sensor and wifi, no displays.

- [getMacAddress.ino](./Arduino/getMacAddress.ino): Connects to the router wifi network, then prints the Arduino MAC address in the Serial Monitor.

#### Technical Details

##### Wifi & Caching

The following wifi protocol and caching system are designed to prevent data from being lost, even if HTTP requests or responses are missed:

The arduino has a cache that stores the logs to send to the lab computer. Conceptually, the arduino cache has two parts. The "old" part of the cache consists of data that has already been sent, but the arduino isn't sure that the computer received it. The "new" part of the cache is data that has not yet been sent.

Every [CACHE_CYCLE_DELAY] milliseconds, the arduino will add a new log to the new part of the cache. When the arduino receives a request from the lab computer, the request comes with a note that says whether or not the computer got the previous request. If so, the arduino will clear the old cache to avoid sending repeat data. Then, the arduino will send the cache via wifi to the computer, and the entire cache will be labeled as "old" (since the data was sent). If the computer did not receive the previous request, the old cache will not be cleared and therefore the data will be resent.

However, it is still possible that repeat data will be sent, for example if the python program is stopped and restarted. The python program will have written the data in the file, but whether it received the last request defaults to "no" on startup. Therefore, on the first request, the python program won't tell the arduino to clear the old cache, and the old cache will be sent again as a repeat log.

A timestamp system is there to prevent this log duplication. Every log that the arduino makes is labeled with the arduino clock value (in milliseconds) at the time of measurement. When the computer receives the logs, it will save the timestamps of those logs inside a hidden file that persists after the python program is stopped. The next time that the computer gets logs, it will check to make sure that the timestamps for those logs do not line up with the ones in the hidden file. That way, the computer can avoid both missing data and repeating measurements in the log files.

##### Smoothing

Currently, the arduino takes measurements from the analog pins every loop cycle. It adds those measurements to an array for smoothing, and gets rid of the oldest measurement in the array. However, those measurements are not a single reading from the analog pin, but rather many readings averaged out to a single value. That way, a higher smoothing value could be achieved with the same amount of memory than by taking single measurements.

For example, with 30 16-byte-integers worth of memory, you could either have an array with 30 measurements, or you could have an array of 15 averages of 15 measurements each. Therefore, the effective smoothing is with 225 values, not just 30.

Also, the readings can be taken close together, since they are taken right after each other instead of waiting for another cycle of the arduino loop function.

##### Behavior on Disconnect

When the display arduino gets disconnected, it will calculate the oxygen and humidity values locally and display those. It won't display the temperature, instead showing "dISC" for disconnected. It will keep caching new data for when it reconnects, though.

## Known Issues and Limitations

- The Arduino clock isn't perfectly accurate, so after a while there may be slightly more or less logs than expected
- Can get repeated logs if you wait a precise amount of time
- Can miss a log if arduino restarted and measured at a precise time (unlikely)
- Can't support multiple sensors of the same type on one glovebox (because it can't differentiate flags)
- Logging untested with daylight savings time
- Non-flexible file structure
- Some computers may stop sending wifi requests when the computer screen turns off

## Links

[Google Drive Folder](https://drive.google.com/drive/folders/1qjnQDnakjW4T2VA_t_dMa19qW6lmA9qH?usp=sharing)

[Full Bill Of Materials](https://docs.google.com/spreadsheets/d/1ikpGfJ6LjHaBAVGgCHs3OJ50SzMK_VNal6e07bsFQgU/edit?usp=sharing)
