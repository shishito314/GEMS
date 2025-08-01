"""
Description:
----------
Architecture, setup, and processes for GEMS system.
Configuration handled upon import according to the specified CONFIG_FILE.
"""
import datetime
import urllib.request
import os
from typing import Dict, List, Any, TextIO, Union

from utilities import *

# -------------------- Constants (Must Match Arduino) --------------------
# Note: for text parsing, flags must contain no spaces
# Sensor flags for text parsing, sending data, and logs.
TEMP_FLAG = "T<"                                                                              # MUST MATCH ARDUINO
OXY_FLAG = "O<"                                                                               # MUST MATCH ARDUINO
WATER_FLAG = "W<"                                                                             # MUST MATCH ARDUINO
LOG_FLAGS = [TEMP_FLAG, OXY_FLAG, WATER_FLAG]                                                 # DON'T NEED MATCH
# ^ LOG_FLAGS doesn't need a corresponding arduino constant,
#   but should contain all the flags for the sensors (like the ones above)

# For Caching
DATA_TRANSFER_SUCCESS_FLAG = "Success"                                                        # MUST MATCH ARDUINO
CACHE_LOG_FLAG = "L:"                                                                         # MUST MATCH ARDUINO
CACHE_REQUEST_FLAG = "Log_"                                                                   # MUST MATCH ARDUINO
REQUEST_RECEIVED_FLAG = "Received"                                                            # MUST MATCH ARDUINO
CACHE_TIME_FLAG = "Time<"                                                                     # MUST MATCH ARDUINO

# Miscellaneous Wifi Communication Flags
DISPLAY_FLAG = "Display_"                                                                     # MUST MATCH ARDUINO
DISPLAY_ERROR_MESSAGE = "Error"                                                               # MUST MATCH ARDUINO

END_FLAG = ">" # For Text Parsing                                                             # MUST MATCH ARDUINO

# -------------------- Other Constants --------------------
DATETIME_STR_LENGTH = 8
# 8 is second precision, 10 is tenth second, 11 hundredth, and so on.

CYCLE_TIMING = 60 # Timing between sending http requests and updating display values
HTTP_WAIT_TIME = 20 # Timeout for an HTTP Request

# Sensor Calculation Variables
SENSE_RESISTANCE = 220 # Resistance in circuit used to calculate the current
VOLT_REF = 4.5 # Maximum voltage read-in by the arduino (voltage that corresponds to 1023)

OXY_CURRENT_MIN = 4 # Minimum current (mA) output by oxygen sensor
OXY_CURRENT_MAX = 20 # Maximum current (mA) output by oxygen sensor
WATER_CURRENT_MIN = 4 # Minimum current (mA) output by water sensor
WATER_CURRENT_MAX = 20 # Maximum current (mA) output by water sensor

OXY_PPM_MIN = 0 # Minimum ppm measured by oxygen sensor
OXY_PPM_MAX = 100 # Maximum ppm measured by oxygen sensor
WATER_DEWPOINT_MIN = -100 # Lowest dewpoint (degrees C) measured by water sensor
WATER_DEWPOINT_MAX = 20 # Highest dewpoint (degrees C) measured by water sensor

OFFSCALE_HIGH_LOG = "HIGH"
OFFSCALE_HIGH_DISPLAY = "HI"
OFFSCALE_LOW_LOG = "LOW"
OFFSCALE_LOW_DISPLAY = "LO"

OFFSCALE_HIGH_MSSG = "HIGH"
OFFSCALE_LOW_MSSG = "LOW"

HTTP_REQUEST_FAIL = "Request Failed"

# ---------- SHOULD NOT CHANGE ----------
CONFIG_FILE = "config.txt"
INTERNAL_DIR = ".internal" # Keeps track of timestamps so they persist between executions of the python script
ERROR_LOG_PREFIX = "errorLog_"
ERROR_LOG_FOLDER = "errors"
LOG_FILE_PREFIX = "log_"
SENSOR_FOLDER_NAMES = {
    OXY_FLAG: "oxy",
    WATER_FLAG: "water",
    TEMP_FLAG: "temp",
}

# -------------------- Classes --------------------
# Sensor classes
class Sensor:
    """Base (Abstract) sensor class"""
    flag: Optional[str] = None  # Flag for HTTP communications and logging
    datatype: Optional[type] = None  # Sensor measurement datatype

    def __init__(self):
        self.glovebox: Optional[Glovebox] = None

    def setGlovebox(self, glovebox: "Glovebox"):
        self.glovebox = glovebox

    def getLog(self):
        """Returns the string that should be printed in the log file"""
        raise NotImplementedError('getLog method not defined')

    def getDisplay(self):
        """Returns the string to be sent to the arduino for displaying"""
        raise NotImplementedError('getDisplay method not defined')

    def addVal(self, val, dateTime):
        """Takes in new measurements and processes them. May include transformation or averaging logic."""
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
            return self.lastValue

    def getDisplay(self):
        try:
            return str(round(self.lastValue, 3))
        except:
            if (self.lastValue):
                return self.lastValue
            else:
                return DISPLAY_ERROR_MESSAGE

    def addVal(self, val, dateTime):
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
            return self.lastValue

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

    def addVal(self, val, dateTime):
        self.lastValue = self.calcOxy(val, dateTime)

    def calcOxy(self, val, dateTime):
        """Calculates ppm O2 from 10-bit arduino voltage measurement, returns string if offscale"""
        current = val / SENSE_RESISTANCE * VOLT_REF / 1023 * 1000
        if current < OXY_CURRENT_MIN:
            self.glovebox.writeError(
                dateTime, [self], "Oxy current offscale low")
            return OFFSCALE_LOW_MSSG
        if current > OXY_CURRENT_MAX:
            self.glovebox.writeError(
                dateTime, [self], "Oxy current offscale high")
            return OFFSCALE_HIGH_MSSG
        ppm = mapValue(OXY_CURRENT_MIN, OXY_CURRENT_MAX,
                       OXY_PPM_MIN, OXY_PPM_MAX, current)
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
            return self.lastValue

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

    def addVal(self, val, dateTime):
        self.lastValue = self.calcWater(val, dateTime)

    def calcWater(self, val, dateTime):
        """Calculates ppm H2O from 10-bit arduino voltage measurement, returns string if offscale"""
        current = val / SENSE_RESISTANCE * VOLT_REF / 1023 * 1000
        if current < WATER_CURRENT_MIN:
            self.glovebox.writeError(
                dateTime, [self], "Water current offscale low")
            return OFFSCALE_LOW_MSSG
        if current > WATER_CURRENT_MAX:
            self.glovebox.writeError(
                dateTime, [self], "Water current offscale high")
            return OFFSCALE_HIGH_MSSG
        dewPoint = mapValue(WATER_CURRENT_MIN, WATER_CURRENT_MAX,
                            WATER_DEWPOINT_MIN, WATER_DEWPOINT_MAX, current)
        exponent = (13.6627 - 2720.84 / (275.38 + dewPoint))
        ppm = pow(10, exponent)
        return ppm

# Arduino
class Arduino:
    def __init__(self, ip: str, isDisplay: bool, sensors: List[Sensor], arduinoIndex: int):
        self.url = f"http://{ip}/"
        self.sensors = sensors
        self.isDisplay = isDisplay
        self.glovebox: Optional["Glovebox"] = None
        self.lastRequestSuccess = False
        self.newData = []
        self.millisReference: Optional[int] = None
        self.dateTimeReference: Optional[datetime.datetime] = None
        self.arduinoIndex = arduinoIndex  # For the internal file

    def setGlovebox(self, glovebox: "Glovebox"):
        """Sets the Arduino's glovebox (Used for error logging)."""
        self.glovebox = glovebox
        for sensor in self.sensors:
            sensor.setGlovebox(glovebox)

    def request(self, message: str):
        try:
            return str(urllib.request.urlopen(self.url + message, timeout=HTTP_WAIT_TIME).read())
        except:
            self.glovebox.writeError(datetime.datetime.now(
            ), self.sensors, f"No HTTP response: {self.url}{message}")
            return HTTP_REQUEST_FAIL

    def convertMillisToDatetimeBefore(self, millis: int):
        """Converts a millis value from Arduino to a datetime, as long as the datetime is before the Arduino's millisReference."""
        if millis > self.millisReference:
            # 4,294,967,295 is the maximum for a uint32_t, which millis is stored as on the arduino
            millis -= 4294967295
        return self.dateTimeReference + datetime.timedelta(milliseconds=millis - self.millisReference)

    def getInternalFilePath(self):
        """Returns the path to the internal directory for this Arduino."""
        return f"./{INTERNAL_DIR}/arduino{str(self.arduinoIndex)}.txt"

    def update(self):
        """Requests and stores the new values from the arduino."""
        self.newData = []
        timeBefore = datetime.datetime.now()
        page = self.request(
            CACHE_REQUEST_FLAG + (DATA_TRANSFER_SUCCESS_FLAG if self.lastRequestSuccess else ""))
        timeAfter = datetime.datetime.now()
        # Approximation for the time the arduino sent response back
        timeAt = timeBefore + ((timeAfter - timeBefore) / 2)
        if (page == HTTP_REQUEST_FAIL) or (not REQUEST_RECEIVED_FLAG in page):
            self.lastRequestSuccess = False
            return
        self.lastRequestSuccess = True
        pageLogs = page.split(CACHE_LOG_FLAG)
        if not len(pageLogs):
            return
        timeHeader = pageLogs[0]
        pageLogs = pageLogs[1:len(pageLogs)]

        if not len(pageLogs):
            return
        if not timeHeader:
            return

        self.dateTimeReference = timeAt
        self.millisReference = int(readFromUntil(
            timeHeader, CACHE_TIME_FLAG, END_FLAG))

        makeDirIfNotExist("./" + INTERNAL_DIR)
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
            arduinoTimeStr = readFromUntilRequireEnd(
                log, CACHE_TIME_FLAG, END_FLAG)

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

            dictionary[CACHE_TIME_FLAG] = self.convertMillisToDatetimeBefore(
                arduinoTime)

            for i in range(0, len(self.sensors)):
                if not self.sensors[i].flag in log:
                    continue
                val = readFromUntil(log, self.sensors[i].flag, END_FLAG)
                self.sensors[i].addVal(self.sensors[i].datatype(
                    val), dictionary[CACHE_TIME_FLAG])
                dictionary[self.sensors[i].flag] = self.sensors[i].getLog()
            self.newData.append(dictionary)

# Glovebox
class Glovebox:
    def __init__(self, name: str, arduinos: List[Arduino]):
        self.name = name
        self.arduinos = arduinos
        self.allSensors: List[Sensor] = []
        for arduino in self.arduinos:
            for sensor in arduino.sensors:
                self.allSensors.append(sensor)
        for i in range(0, len(self.arduinos)):
            self.arduinos[i].setGlovebox(self)

    def makeLogLine(self, data: Dict[str, Any], sensor: Union[Sensor, type[Sensor]]):
        """Returns the string for a new line of the log file given the passed data"""
        line = getTimeStr(data[CACHE_TIME_FLAG])
        if (sensor.flag in data):
            line += (" " + data[sensor.flag])
        line.rstrip()
        line += "\n"
        return line

    def writeNewLogLine(self, logFile: TextIO, data: Dict[str, Any], sensor: Union[Sensor, type[Sensor]]):
        """Writes a new line in the log file for the passed data."""
        logFile.write(self.makeLogLine(data, sensor))

    def writeError(self, dateTime: datetime.datetime, sensorsAffected: List[Sensor], message: str):
        """Writes an error to the error log file"""
        makeDirIfNotExist(self.getErrorFolderPath())
        with open(self.getErrorLogPathWithDateTime(dateTime), "a") as file:
            errorStr = f"{getTimeStr(dateTime)} [ "
            for sensor in sensorsAffected:
                errorStr += sensor.__class__.__name__ + " "
            errorStr += f"] {message}\n"
            file.write(errorStr)

    def getSensorFolderPath(self, sensorType: Union[Sensor, type[Sensor]]) -> str:
        """Returns the folder for the log files of the specified glovebox and sensor"""
        return f"./{self.name}/{SENSOR_FOLDER_NAMES[sensorType.flag]}"

    def getErrorFolderPath(self) -> str:
        """Returns the folder for the error files of this glovebox"""
        return f"./{self.name}/{ERROR_LOG_FOLDER}"

    def getLogFilePathWithDateTime(self, dateTime: datetime.datetime, sensor: Union[Sensor, type[Sensor]]):
        """Returns the log file for this glovebox and the given datetime"""
        return f"./{self.name}/{SENSOR_FOLDER_NAMES[sensor.flag]}/{LOG_FILE_PREFIX}{str(dateTime)[0:10]}.txt"

    def getErrorLogPathWithDateTime(self, dateTime: datetime.datetime):
        """Returns the error file for this glovebox and the given datetime"""
        return f"./{self.name}/{ERROR_LOG_FOLDER}/{ERROR_LOG_PREFIX}{str(dateTime)[0:10]}.txt"

    def update(self):
        """Gets new sensor values, logs them, and sends display values"""
        # Get new data
        allNewData = []
        for arduino in self.arduinos:
            arduino.update()
            allNewData.extend(arduino.newData)
        allNewData.sort(key=lambda d: d[CACHE_TIME_FLAG])

        if not len(allNewData):
            return

        # Log data
        makeDirIfNotExist("./" + self.name)

        for sensor in self.allSensors:
            makeDirIfNotExist(
                f"./{self.name}/{SENSOR_FOLDER_NAMES[sensor.flag]}")

            for log in allNewData:
                if log[sensor.flag]:
                    logFileName = self.getLogFilePathWithDateTime(
                        log[CACHE_TIME_FLAG], sensor)
                    with open(logFileName, "a") as logFile:
                        self.writeNewLogLine(logFile, log, sensor)

        # Send display values to arduino
        displayStr = DISPLAY_FLAG
        for sensor in self.allSensors:
            displayStr += sensor.flag
            displayStr += sensor.getDisplay()
            displayStr += END_FLAG

        for arduino in self.arduinos:
            if arduino.isDisplay:
                arduino.request(displayStr)

# -------------------- Utility Functions --------------------
def getGloveboxByName(name: str) -> Glovebox:
    """Returns the Glovebox object for the glovebox with the specified name"""
    return gloveboxes[gloveboxNames.index(name)]

def isLogFile(fileName: str) -> bool:
    """Tests a string to see if it follows the format for a log file"""
    if len(fileName) < len(LOG_FILE_PREFIX) + 10:
        return False
    if fileName[0:len(LOG_FILE_PREFIX)] != LOG_FILE_PREFIX:
        return False
    try:
        strToDate(fileName[len(LOG_FILE_PREFIX):len(LOG_FILE_PREFIX) + 10])
    except:
        return False
    return True

def isErrorFile(fileName: str) -> bool:
    """Tests a string to see if it follows the format for an error file"""
    if len(fileName) < len(ERROR_LOG_PREFIX) + 10:
        return False
    if fileName[0:len(ERROR_LOG_PREFIX)] != ERROR_LOG_PREFIX:
        return False
    try:
        strToDate(fileName[len(ERROR_LOG_PREFIX):len(ERROR_LOG_PREFIX) + 10])
    except:
        return False
    return True

def getDateTimeStr(time: datetime.datetime) -> str:
    """Returns a string representing the given datetime."""
    return str(time)[0:11 + DATETIME_STR_LENGTH]

def getTimeStr(time: datetime.datetime) -> str:
    """Returns a string representing the time part of the given datetime."""
    return str(time)[11:11 + DATETIME_STR_LENGTH]

def getTimeFromLogLine(line: str) -> datetime.time:
    """Returns the time of day from the given line of a log or error file"""
    return strToTime(line[0:DATETIME_STR_LENGTH])

def getDateFromLogFileName(fileName: str) -> datetime.date:
    """Returns the date from the given log file name"""
    return strToDate(fileName[len(LOG_FILE_PREFIX):len(LOG_FILE_PREFIX) + 10])

def getDateFromErrorFileName(fileName: str) -> datetime.date:
    """Returns the date from the given error file name"""
    return strToDate(fileName[len(ERROR_LOG_PREFIX):len(ERROR_LOG_PREFIX) + 10])


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
    "Temp": Temp,
    "Oxy": Oxy,
    "Water": Water
}

gloveboxes: List[Glovebox] = []  # List of all gloveboxes
# Names of all the gloveboxes, in identical order as the gloveboxes list (used for getGloveboxByName utility)
gloveboxNames: List[str] = []

# Fail if no config file
assert os.path.exists(CONFIG_FILE), f"Config file \"{CONFIG_FILE}\" not found."

with open(CONFIG_FILE, "r") as configFile:
    configFileStr = configFile.read()
# File Parsing
configBoxes = configFileStr.split(CONFIG_GLOVEBOX_FLAG)
# Since the config file should start with a glovebox flag
configBoxes = configBoxes[1:len(configBoxes)]
arduinoIndex = 0
for configBox in configBoxes:
    name = removeSpaces(readUntil(configBox, "\n"))
    arduinoLines = configBox.split(CONFIG_ARDUINO_FLAG)
    # Since the arduino lines should start with an arduino flag
    arduinoLines = arduinoLines[1:len(arduinoLines)]
    # Generate list of arduinos for the glovebox
    arduinos = []
    for line in arduinoLines:
        # Parse arduino IP address
        ip = removeSpaces(readFromUntil(
            line, CONFIG_IP_FLAG, CONFIG_DISPLAY_FLAG))
        # Parse whether arduino displays
        displayStr = removeSpaces(readFromUntil(
            line, CONFIG_DISPLAY_FLAG, CONFIG_SENSORS_FLAG))
        if displayStr == CONFIG_DISPLAY_TRUE_FLAG:
            display = True
        elif displayStr == CONFIG_DISPLAY_FALSE_FLAG:
            display = False
        else:
            raise SyntaxError(
                "Display value listed in config that was not recognized")
        # Generate list of sensors
        sensors = []
        sensorFlags = readFrom(line, CONFIG_SENSORS_FLAG).split()
        for flag in sensorFlags:
            if flag in SENSOR_CONFIG_FLAG_TO_CLASS:
                # Initialize sensor class corresponding to sensor flag
                sensors.append(SENSOR_CONFIG_FLAG_TO_CLASS[flag]())
            else:
                raise SyntaxError(
                    "Sensor listed in config that was not recognized")
        arduinos.append(Arduino(ip, display, sensors, arduinoIndex))
        arduinoIndex += 1
    gloveboxes.append(Glovebox(name, arduinos))
    gloveboxNames.append(name)

# Fail if no gloveboxes
assert gloveboxes, f"No gloveboxes parsed from config file \"{CONFIG_FILE}.\""
