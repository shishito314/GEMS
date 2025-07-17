# -------------------- File Description --------------------
# This file contains the architecture and setup needed for the gems system,
# including classes and update methods for the gloveboxes, arduinos, and sensors.
# It sets up the architecture based off of the config.txt file, and will parse that
# file for setup upon import.

import urllib.request # for sending http requests to arduinos
import datetime # for getting the time
import os # for checking file existence
from utilities import *

# -------------------- Constants (Must Match Arduino) --------------------

# Note: for text parsing, flags must contain no spaces
TEMP_FLAG = "Temp:" # For text parsing, sending data, and logs.                               MUST MATCH ARDUINO
OXY_FLAG = "Oxy:" # For text parsing, sending data, and logs.                                 MUST MATCH ARDUINO
WATER_FLAG = "Water:" # For text parsing, sending data, and logs.                             MUST MATCH ARDUINO
LOG_FLAGS = [TEMP_FLAG, OXY_FLAG, WATER_FLAG] # For log file parsing (Used in data.py)        NO MATCH
# ^ LOG_FLAGS doesn't need a corresponding arduino constant, but should contain all the flags for the sensors (like the ones above)

# For Caching
DATA_TRANSFER_SUCCESS_FLAG = "Success" # Sent to confirm successfully recieved cache request  MUST MATCH ARDUINO
CACHE_LOG_FLAG = "Log:" # For parsing logs from the Arduino HTTP response                     MUST MATCH ARDUINO
CACHE_REQUEST_FLAG = "Log_" # Used to let the Arduino know we want it's cache data            MUST MATCH ARDUINO
REQUEST_RECEIVED_FLAG = "Received" # Sent by the arduino to confirm it got the cache request  MUST MATCH ARDUINO
CACHE_TIME_FLAG = "Time:" # For dictionaries and sent by the arduino to give the millis time  MUST MATCH ARDUINO

# Miscellaneous Wifi Communication Flags
DISPLAY_FLAG = "Display_" # For sending display data to the arduino.                          MUST MATCH ARDUINO
DISPLAY_ERROR_MESSAGE = "Error" # What should be sent to the arduino in the case of an error  MUST MATCH ARDUINO

END_FLAG = "End" # An end flag used for text parsing                                          MUST MATCH ARDUINO

# -------------------- Other Constants --------------------
# ---------- MAY BE CHANGED ----------
DATETIME_STR_LENGTH = 21 # How to trim the datetime string for the desired precision.
# 19 is second precision, 21 is tenth second, 22 hundredth, and so on.

CYCLE_TIMING = 15 # Timing between sending http requests and updating display values
# (may be different than logging cycle, which depends on the caching cycle time in the arduino code)
HTTP_WAIT_TIME = CYCLE_TIMING / 3 # To keep cycling on schedule
# max wait should be this x3 - in box arduino, out of box arduino, out of box arduino (for displays)

# Sensor Calculation Variables
SENSE_RESISTANCE = 220 # Resistance in circuit used to calculate the current
VOLT_REF = 5 # Maximum voltage read-in by the arduino (voltage that corresponds to 1023)

OXY_CURRENT_MIN = 4 # Minimum current (mA) output by the oxygen sensor
OXY_CURRENT_MAX = 20 # Maximum current (mA) output by the oxygen sensor
WATER_CURRENT_MIN = 4 # Minimum current (mA) output by the water sensor
WATER_CURRENT_MAX = 20 # Maximum current (mA) output by the water sensor

OXY_PPM_MIN = 0 # Minimum ppm measured by the oxygen sensor
OXY_PPM_MAX = 100 # Maximum ppm measured by the oxygen sensor
WATER_DEWPOINT_MIN = -100 # Lowest dewpoint measured by the water sensor
WATER_DEWPOINT_MAX = 20 # Highest dewpoint measured by the water sensor

OFFSCALE_HIGH_LOG = "HIGH"
OFFSCALE_HIGH_DISPLAY = "HI"
OFFSCALE_LOW_LOG = "LOW"
OFFSCALE_LOW_DISPLAY = "LO"

OFFSCALE_HIGH_MSSG = "HIGH" # Used internally to record offscale high
OFFSCALE_LOW_MSSG = "LOW" # Used internally to record offscale low

HTTP_REQUEST_FAIL = "Request Failed" # Used internally for detecting failed HTTP request

# ---------- SHOULD NOT CHANGE ----------
CONFIG_FILE = "config.txt" # Name for the config file
INTERNAL_DIR = ".internal" # Keeps track of timestamps so they persist between executions of the python script
ERROR_LOG_FILE = "errorLog" # Name for the error log file
LOG_FILE_PREFIX = "log_"
SENSOR_FOLDER_NAMES = {
  OXY_FLAG: "oxy",
  WATER_FLAG: "water",
  TEMP_FLAG: "temp",
}

# -------------------- Classes --------------------
# Sensor classes
# Base (Abstract) sensor class
class Sensor:
  # Static variables that every Sensor type should have
  flag = None # Flag to be used in HTTP communications and logging
  datatype = None # The datatype of the sensor measurements (e.g. float)

  def __init__(self):
    self.glovebox = None # the glovebox that the sensor belongs to. Used for logging errors.
  # Sets the sensor's glovebox 
  def setGlovebox(self, glovebox):
    self.glovebox = glovebox

  # getLog should return the string that should be printed in the log file
  def getLog(self):
    raise NotImplementedError('getLog method not defined')
  # getDisplay should return the string to be sent to the arduino for displaying
  def getDisplay(self):
    raise NotImplementedError('getDisplay method not defined')
  # addVal is used to take in new measurements,
  # and may (for example) add them to a moving average data structure.
  # Any calculations needed to go from the value sent by the arduino
  # to the real world measurement may also be done here
  def addVal(self, val):
    raise NotImplementedError('addVal method not defined')
  
class Temp(Sensor):
  flag = TEMP_FLAG
  datatype = float

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

class Oxy(Sensor):
  flag = OXY_FLAG
  datatype = float

  def __init__(self):
    super().__init__()
    self.lastValue = None

  def getLog(self):
    if self.lastValue == OFFSCALE_HIGH_MSSG:
      return OFFSCALE_HIGH_LOG
    elif self.lastValue == OFFSCALE_LOW_MSSG:
      return OFFSCALE_LOW_LOG
    try:
      return str(round(self.lastValue, 3))
    except:
      try:
        return self.lastValue
      except:
        return "Error"
  
  def getDisplay(self):
    if self.lastValue == OFFSCALE_HIGH_MSSG:
      return OFFSCALE_HIGH_DISPLAY
    elif self.lastValue == OFFSCALE_LOW_MSSG:
      return OFFSCALE_LOW_DISPLAY
    try:
      return str(round(self.lastValue, 3))
    except:
      if (self.lastValue):
        return self.lastValue
      else:
        return DISPLAY_ERROR_MESSAGE
  
  def addVal(self, val):
    self.lastValue = self.calcOxy(val)
  
  # Helper function for calculating oxygen ppm from 10-bit arduino voltage measurement
  def calcOxy(self, val):
    current = val / SENSE_RESISTANCE * VOLT_REF / 1023 * 1000
    if current < OXY_CURRENT_MIN:
      self.glovebox.writeError(getCurrentDatetimeStr(), "The current calculated for the oxygen sensor is lower than the threshold")
      return OFFSCALE_LOW_MSSG
    if current > OXY_CURRENT_MAX:
      self.glovebox.writeError(getCurrentDatetimeStr(), "The current calculated for the oxygen sensor is higher than the threshold")
      return OFFSCALE_HIGH_MSSG
    ppm = map(OXY_CURRENT_MIN, OXY_CURRENT_MAX, OXY_PPM_MIN, OXY_PPM_MAX, current)
    return ppm

class Water(Sensor):
  flag = WATER_FLAG
  datatype = float

  def __init__(self):
    super().__init__()
    self.lastValue = None

  def getLog(self):
    if self.lastValue == OFFSCALE_HIGH_MSSG:
      return OFFSCALE_HIGH_LOG
    elif self.lastValue == OFFSCALE_LOW_MSSG:
      return OFFSCALE_LOW_LOG
    try:
      return str(round(self.lastValue, 3))
    except:
      try:
        return self.lastValue
      except:
        return "Error"
  
  def getDisplay(self):
    if self.lastValue == OFFSCALE_HIGH_MSSG:
      return OFFSCALE_HIGH_DISPLAY
    elif self.lastValue == OFFSCALE_LOW_MSSG:
      return OFFSCALE_LOW_DISPLAY
    try:
      return str(round(self.lastValue, 3))
    except:
      if (self.lastValue):
        return self.lastValue
      else:
        return DISPLAY_ERROR_MESSAGE

  def addVal(self, val):
    self.lastValue = self.calcWater(val)

  # Helper function for calculating Water ppm from 10-bit arduino voltage measurement
  def calcWater(self, val):
    current = val / SENSE_RESISTANCE * VOLT_REF / 1023 * 1000
    if current < WATER_CURRENT_MIN:
      self.glovebox.writeError(getCurrentDatetimeStr(), "The current calculated for the dewpoint sensor is lower than the threshold")
      return OFFSCALE_LOW_MSSG
    if current > WATER_CURRENT_MAX:
      self.glovebox.writeError(getCurrentDatetimeStr(), "The current calculated for the dewpoint sensor is higher than the threshold")
      return OFFSCALE_HIGH_MSSG
    dewPoint = map(WATER_CURRENT_MIN, WATER_CURRENT_MAX, WATER_DEWPOINT_MIN, WATER_DEWPOINT_MAX, current)
    exponent = (13.6627 - 2720.84 / (275.38 + dewPoint))
    ppm = pow(10, exponent)
    return ppm

# Arduino
class Arduino:
  def __init__(self, ip, isDisplay, sensors, arduinoIndex):
    self.url = "http://" + ip + "/"
    self.sensors = sensors
    self.isDisplay = isDisplay
    self.glovebox = None
    self.lastRequestSuccess = False
    self.newData = []
    self.millisReference = None
    self.datetimeReference = None
    self.arduinoIndex = arduinoIndex # For the internal file

  # Sets the Arduino's glovebox (Used for error logging)
  def setGlovebox(self, glovebox):
    self.glovebox = glovebox
    for sensor in self.sensors:
      sensor.setGlovebox(glovebox)
  
  # Sends a request with the given message
  def request(self, message):
    # lastRequestSuccess = True
    try:
      return str(urllib.request.urlopen(self.url + message, timeout=HTTP_WAIT_TIME).read())
    except:
      self.glovebox.writeError(getCurrentDatetimeStr(), "Did not recieve HTTP response from " + self.url + message)
      return HTTP_REQUEST_FAIL
  
  # Takes a millis value and converts it to a datetime with the arduino's references
  # The datetime will always be the same as or before the millisReference
  # (since the timestamp for the request from the arduino should be after all the other timestamps)
  # As long as the millis isn't from some 98 days before (2x the 49 day span), it should be accurate
  def convertMillisToDatetimeBefore(self, millis):
    if millis > self.millisReference:
      millis -= 4294967295 # 4,294,967,295 is the maximum for a uint32_t, which millis is stored as on the arduino
    return self.datetimeReference + datetime.timedelta(milliseconds = millis - self.millisReference)
    
  def getInternalFilePath(self):
    # Using arduinoIndex instead of, (for example) an IP identifier
    # so that the IP can get changed without causing file buildup in the internal directory
    return "./" + INTERNAL_DIR + "/Arduino" + str(self.arduinoIndex) + ".txt"

  # Requests and stores the new values from the arduino.
  def update(self):
    self.newData = [] # clear newData
    timeBefore = datetime.datetime.now() # trying to do this as close to the request time as possible
    page = self.request(CACHE_REQUEST_FLAG + (DATA_TRANSFER_SUCCESS_FLAG if self.lastRequestSuccess else ""))
    print()
    print(page)
    print()
    timeAfter = datetime.datetime.now() # trying to do this as close to the request time as possible
    timeAt = timeBefore + ((timeAfter-timeBefore) / 2) # Approximation for the time the arduino sent response back
    if (page == HTTP_REQUEST_FAIL) or (not REQUEST_RECEIVED_FLAG in page):
      self.lastRequestSuccess = False
      return
    # Otherwise, had a successful request
    self.lastRequestSuccess = True
    pageLogs = page.split(CACHE_LOG_FLAG)
    if not len(pageLogs): return
    timeHeader = pageLogs[0]
    pageLogs = pageLogs[1:len(pageLogs)]

    if not len(pageLogs): return
    if not timeHeader: return

    self.datetimeReference = timeAt
    self.millisReference = int(readFromUntil(timeHeader, CACHE_TIME_FLAG, END_FLAG))

    if not os.path.isdir("./" + INTERNAL_DIR):
      os.mkdir("./" + INTERNAL_DIR) # creating internal folder if it doesn't exist
    internalFileName = self.getInternalFilePath()
    if os.path.isfile(internalFileName):
      with open(internalFileName, "r") as internalFile:
        internalFileStr = internalFile.read()
    else:
      internalFileStr = ""
    internalFileLines = internalFileStr.splitlines()
    
    with open(internalFileName, "w") as internalFile:
      internalFile.seek(0)
      internalFile.truncate()

    for i in range(0, len(pageLogs)):
      log = pageLogs[i]
      dictionary = {}
      arduinoTimeStr = readFromUntilRequireEnd(log, CACHE_TIME_FLAG, END_FLAG)
      print(str(self.convertMillisToDatetimeBefore(int(arduinoTimeStr))))

      # If the arduino had to trim the end of the cache string for memory,
      # it is possible that it could get trimmed in the middle of the millis value,
      # causing an incorrect timestamp. If the end flag for the timestamp isn't found,
      # (indicative that this happened), then the log will just be skipped.
      if not arduinoTimeStr:
        continue
      
      with open(internalFileName, "a") as internalFile:
        internalFile.write(arduinoTimeStr + "\n")

      repeatLog = False
      for line in internalFileLines:
        if arduinoTimeStr == line:
          repeatLog = True
          break
      if repeatLog:
        continue
      arduinoTime = int(arduinoTimeStr)

      dictionary[CACHE_TIME_FLAG] = self.convertMillisToDatetimeBefore(arduinoTime)

      for i in range(0, len(self.sensors)):
        if not self.sensors[i].flag in log: continue
        val = readFromUntil(log, self.sensors[i].flag, END_FLAG)
        self.sensors[i].addVal(self.sensors[i].datatype(val))
        dictionary[self.sensors[i].flag] = self.sensors[i].getLog()
      self.newData.append(dictionary)

# Glovebox
class Glovebox:
  def __init__(self, name, arduinos):
    self.name = name
    self.arduinos = arduinos
    self.allSensors = [] # a list holding all the sensors under the glovebox
    for arduino in self.arduinos:
      for sensor in arduino.sensors:
        self.allSensors.append(sensor)
    for i in range(0, len(self.arduinos)):
      self.arduinos[i].setGlovebox(self) # setting each of the arduino's glovebox as this one

  # Helper function for writing the new line of the log file for the passed data.
  def writeNewLogLine(self, logFile, data, sensor):
    logFile.write(self.makeLogLine(data, sensor))

  # Returns the string for a new line of the log file given the passed data
  def makeLogLine(self, data, sensor):
    line = getDatetimeStr(data[CACHE_TIME_FLAG])
    # for sensor in self.allSensors:
    if (sensor.flag in data):
      line += (" " + sensor.flag + " " + data[sensor.flag])
    while(line[len(line) - 1] == " "): # Remove unecessary trailing spaces
      line = line[0:len(line) - 1]
    line += "\n"
    return line

  # Gets today's logfile for this glovebox
  def getLogFilePathWithDateTime(self, dateTime, sensor):
    return "./" + self.name + "/" + SENSOR_FOLDER_NAMES[sensor.flag] + "/" + LOG_FILE_PREFIX + str(dateTime)[0:10] + ".txt"  

  def getErrorLogPath(self):
    return "./" + self.name + "/" + ERROR_LOG_FILE + ".txt"

  # Gets new sensor values, logs them, and sends display values
  def update(self):
    allNewData = []
    for arduino in self.arduinos:
      arduino.update()
      allNewData.extend(arduino.newData)
    sortDictionariesByValue(allNewData, CACHE_TIME_FLAG)

    if (not len(allNewData)):
      return

    if not os.path.isdir("./" + self.name):
      os.mkdir("./" + self.name) # creating the folder for this glovebox if it doesn't exist already

    for sensor in self.allSensors:
      if not os.path.isdir("./" + self.name + "/" + SENSOR_FOLDER_NAMES[sensor.flag]):
        os.mkdir("./" + self.name + "/" + SENSOR_FOLDER_NAMES[sensor.flag]) # creating the folder for this sensor if it doesn't exist already

      for log in allNewData:
        if log[sensor.flag]:
          logFileName = self.getLogFilePathWithDateTime(log[CACHE_TIME_FLAG], sensor) # this way, the logfiles get split by day
          with open(logFileName, "a") as logFile:
            self.writeNewLogLine(logFile, log, sensor)

    # Sending display values to arduino
    displayStr = DISPLAY_FLAG
    for sensor in self.allSensors:
      displayStr += sensor.flag
      displayStr += sensor.getDisplay()
      displayStr += END_FLAG

    for arduino in self.arduinos:
      if arduino.isDisplay:
        arduino.request(displayStr)

  # used for writing an error to the error log file
  def writeError(self, timeStr, message):
    if not os.path.isdir("./" + self.name):
      os.mkdir("./" + self.name)
    with open(self.getErrorLogPath(), "a") as file:
      file.write(timeStr)
      file.write("  ")
      file.write(message)
      file.write("\n")

# -------------------- Utility Functions --------------------
# Gets a string representing the current date and time.
def getCurrentDatetimeStr():
  return str(datetime.datetime.now())[0:DATETIME_STR_LENGTH]
# Gets a string representing the given datetime.
def getDatetimeStr(time):
  return str(time)[0:DATETIME_STR_LENGTH]
# Gets the folder for the log files of the specified glovebox and sensor
def getSensorFolderName(glovebox, sensorFlag):  
  return "./" + glovebox.name + "/" + SENSOR_FOLDER_NAMES[sensorFlag]
# Tests a string to see if it follows the format for a logFile
def isLogFile(fileName):
  if len(fileName) < len(LOG_FILE_PREFIX) + 10:
    return False
  if fileName[0:len(LOG_FILE_PREFIX)] != LOG_FILE_PREFIX:
    return False
  try:
    convertStrToDate(fileName[len(LOG_FILE_PREFIX):len(LOG_FILE_PREFIX) + 10])
  except:
    return False
  return True
# Gets the Glovebox object for the glovebox with the specified name
def getGloveboxByName(name) -> Glovebox:
  return gloveboxes[gloveboxNames.index(name)]

# -------------------- Set Up Class Instances With Config File --------------------
# ---------- Config Constants ----------
CONFIG_GLOVEBOX_FLAG = "Glovebox: "
CONFIG_ARDUINO_FLAG = "Arduino: "
CONFIG_IP_FLAG = "IP:"
CONFIG_DISPLAY_FLAG = "Display:"
CONFIG_SENSORS_FLAG = "Sensors:"
CONFIG_DISPLAY_TRUE_FLAG = "True"
CONFIG_DISPLAY_FALSE_FLAG = "False"
SENSOR_CONFIG_FLAG_TO_CLASS = {
  "Temp" : Temp,
  "Oxy" : Oxy,
  "Water" : Water
}

gloveboxes = [] # List of all gloveboxes
gloveboxNames = [] # Names of all the gloveboxes, in identical order as the gloveboxes list (used for getGloveboxByName utility)
with open(CONFIG_FILE, "r") as configFile:  
  configFileStr = configFile.read()
# File Parsing
configBoxes = configFileStr.split(CONFIG_GLOVEBOX_FLAG)
configBoxes = configBoxes[1:len(configBoxes)] # Since the config file should start with a glovebox flag
arduinoIndex = 0
for configBox in configBoxes:
  name = removeSpaces(readUntil(configBox, "\n")) # parse out the glovebox name
  arduinoLines = configBox.split(CONFIG_ARDUINO_FLAG)
  arduinoLines = arduinoLines[1:len(arduinoLines)] # Since the arduino lines should start with an arduino flag
  # Generate list of arduinos for the glovebox
  arduinos = []
  for line in arduinoLines:
    # Parse out arduino IP address
    ip = removeSpaces(readFromUntil(line, CONFIG_IP_FLAG, CONFIG_DISPLAY_FLAG))
    # Parse out if arduino should display or not
    displayStr = removeSpaces(readFromUntil(line, CONFIG_DISPLAY_FLAG, CONFIG_SENSORS_FLAG))
    if displayStr == CONFIG_DISPLAY_TRUE_FLAG:
      display = True
    elif displayStr == CONFIG_DISPLAY_FALSE_FLAG:
      display = False
    else:
      raise SyntaxError("Display value listed in config that was not recognized")
    # Generate list of sensors
    sensors = []
    sensorFlags = readFrom(line, CONFIG_SENSORS_FLAG).split() # splits on spaces
    for flag in sensorFlags:
      if flag in SENSOR_CONFIG_FLAG_TO_CLASS:
        sensors.append(SENSOR_CONFIG_FLAG_TO_CLASS[flag]()) # Initialize the sensor class corresponding to the sensor flag
      else:
        raise SyntaxError("Sensor listed in config that was not recognized")
    arduinos.append(Arduino(ip, display, sensors, arduinoIndex)) # adding the arduino to the list of arduinos for the glovebox
    arduinoIndex += 1
  gloveboxes.append(Glovebox(name, arduinos)) # adding the glovebox to the list of gloveboxes
  gloveboxNames.append(name) # adding to glovebox's name to the gloveboxNames list
