# -------------------- File Description --------------------
# This is the file containing the data utilities for 
# These utilities can be used for analysis, plotting, etc.
# Right now, it expects the log files to be in glovebox-named folders,
# with those folders in the same directory as this script.

from gems import *
import matplotlib.pyplot as plt
from matplotlib import *
import os

# -------------------- Constants --------------------
DATA_TIME_FLAG = "Time"
DATA_MEASUREMENTS_FLAG = "Data:"

# -------------------- Internal Utilities --------------------
def logIsBefore(line, time):
  return convertStrToDatetime(line[0:DATETIME_STR_LENGTH]) < time

# -------------------- Getting Data --------------------
# ---------- Data Format ----------
# Functions that get a specific sensor's data will return a dictionary with a list of timestamps
# under the key DATA_TIME_FLAG, and a list of measurements under the key of DATA_MEASUREMENTS_FLAG.
# The timestamps correspond to the measurements in order
# (e.g. data[DATA_TIME_FLAG][2] is the timestamp for the data[DATA_MEASUREMENTS_FLAG][2])

# Functions that get data for all sensors will return a dictionary with sub-dictionaries under the sensor flags as keys.
# The sub-dictionaries follow the same format as the data returned by the single-sensor functions
# For example, to get the list of Temperature measurements, you could write data[TEMP_FLAG][DATA_MEASUREMENTS_FLAG]

# For all data functions, the flag "keepErrors" decides whether or not to keep logs that can't be converted
# to the sensorType's datatype (e.g. "HIGH" and "LOW"). If true, they will be put into the data as raw strings.

# ---------- Data Utility Functions ----------
# get data from the last [numEntries] entries
def getLastNMeasurements(glovebox: Glovebox, numEntries, sensorType, keepErrors=False):
  data = {
    DATA_TIME_FLAG: [],
    DATA_MEASUREMENTS_FLAG: []
  }

  sensorFolderName = getSensorFolderName(glovebox, sensorType.flag)

  if os.path.isdir(sensorFolderName):
    # gets the files inside the sensor's folder in reverse alphabetical order
    fileNames = sorted(os.listdir(sensorFolderName), reverse=True)
    # Find the most recent log file (relies on reverse alphabetic order)
    logFilePath = None
    for fileName in fileNames:
      if isLogFile(fileName):
        logFilePath = sensorFolderName + "/" + fileName
        break
    if not logFilePath:
      return data
  else:
    return data
  
  with open(logFilePath, "r") as file:
    logLines = file.read().splitlines()
  logLines = logLines[len(logLines) - numEntries:len(logLines)]
  for line in logLines:
    try:
      time = convertStrToDatetime(line[0:DATETIME_STR_LENGTH])
    except:
      continue
    try:
      # using datatype to construct/cast the string from the logfile to the desired type
      # If the flag is the last in the line, will just return everything after it
      data[DATA_MEASUREMENTS_FLAG].append(sensorType.datatype(removeSpaces(readFrom(line, sensorType.flag))))
      data[DATA_TIME_FLAG].append(time)
    except:
      if (keepErrors):
        data[DATA_MEASUREMENTS_FLAG].append(removeSpaces(readFrom(line, sensorType.flag)))
        data[DATA_TIME_FLAG].append(time)
      else:
        continue
      # raise TypeError("Invalid datatype when trying to getDataLastLines. Flag: " + sensorType.flag + " Datatype: " + str(sensorType.datatype))
  return data
# get data for all sensors from the last [numEntries] entries
# logFile defaults to None, signifying the logFile for the current date
def getLastNMeasurementsAllSensors(glovebox: Glovebox, numEntries, keepErrors=False):
  data = {}
  for sensor in glovebox.allSensors:
    data[sensor.flag] = getLastNMeasurements(glovebox, numEntries, sensor, keepErrors)
  return data

def getLastMeasurement(glovebox: Glovebox, sensorType, keepErrors=False):
  data = {
    DATA_TIME_FLAG: None,
    DATA_MEASUREMENTS_FLAG: None
  }

  sensorFolderName = getSensorFolderName(glovebox, sensorType.flag)

  if os.path.isdir(sensorFolderName):
    # gets the files inside the sensor's folder in reverse alphabetical order
    fileNames = sorted(os.listdir(sensorFolderName), reverse=True)
    # Find the most recent log file (relies on reverse alphabetic order)
    logFilePath = None
    for fileName in fileNames:
      if isLogFile(fileName):
        logFilePath = sensorFolderName + "/" + fileName
        break
    if not logFilePath:
      return data
  else:
    return data
  
  with open(logFilePath, "r") as file:
    logLines = file.read().splitlines()
    lineIndex = len(logLines) - 1

  while lineIndex >= 0:
    line = logLines[lineIndex]
    try:
      time = convertStrToDatetime(line[0:DATETIME_STR_LENGTH])
    except:
      lineIndex -= 1
      continue
    try:
      # using datatype to construct/cast the string from the logfile to the desired type
      # If the flag is the last in the line, will just return everything after it
      data[DATA_MEASUREMENTS_FLAG] = sensorType.datatype(removeSpaces(readFrom(line, sensorType.flag)))
      data[DATA_TIME_FLAG] = time
      break
    except:
      if (keepErrors):
        data[DATA_MEASUREMENTS_FLAG] = removeSpaces(readFrom(line, sensorType.flag))
        data[DATA_TIME_FLAG] = time
        break
      else:
        lineIndex -= 1
        continue
      # raise TypeError("Invalid datatype when trying to getDataLastLines. Flag: " + sensorType.flag + " Datatype: " + str(sensorType.datatype))
  return data

def getLastMeasurementAllSensors(glovebox: Glovebox, keepErrors=False):
  data = {}
  for sensor in glovebox.allSensors:
    data[sensor.flag] = getLastMeasurement(glovebox, sensor, keepErrors)
  return data

# Gets data from the given start time to the endTime.
# startTime is inclusive, endTime is exclusive
def getDataByTime(glovebox: Glovebox, startTime: datetime.datetime, endTime: datetime.datetime, sensorType, keepErrors=False):
  if (endTime < startTime):
    raise ValueError("getDataByTime: endTime is before startTime")
  # initialize the structure for data
  data = {
    DATA_TIME_FLAG: [],
    DATA_MEASUREMENTS_FLAG: []
  }

  sensorFolderName = getSensorFolderName(glovebox, sensorType.flag)

  # get a list of the log files for the glovebox
  if not os.path.isdir(sensorFolderName):
    return data # no data
  fileNames = os.listdir(sensorFolderName)
  logFiles = []
  # remove other files, like ErrorLog.txt, and empty files
  for fileName in fileNames:
    if isLogFile(fileName):
      logFiles.append(fileName)
  logFiles.sort()

  if not len(logFiles):
    return data

  logFileIndex = 0
  logFileName = logFiles[logFileIndex]
  date = convertStrToDate(logFileName[len(LOG_FILE_PREFIX):len(LOG_FILE_PREFIX)+10])
  # loop through log files to find the first one that might have data in the desired time range
  while date < startTime.date() and logFileIndex < len(logFiles) - 1:
    logFileIndex += 1
    logFileName = logFiles[logFileIndex]
    date = convertStrToDate(logFileName[len(LOG_FILE_PREFIX):len(LOG_FILE_PREFIX)+10])
  # combine used to convert date to datetime
  if datetime.datetime.combine(date, datetime.time.min) > endTime or logFileIndex >= len(logFiles):
    return data # no data
  
  logFilePath = os.path.join(sensorFolderName, logFileName)

  # get log data as text
  with open(logFilePath, "r") as log:
    logStr = log.read()
  logLines = logStr.splitlines()
  lineIndex = 0
  line = logLines[0]

  # Looping through the lines until we get to lines we want to start adding to the data (i.e. lines after the startTime)
  try:
    isBeforeStart = logIsBefore(line, startTime) # so we can try/except in the loop
  except:
    isBeforeStart = True
  while isBeforeStart:
    lineIndex += 1
    if (lineIndex >= len(logLines)):
      break
    line = logLines[lineIndex]
    try:
      isBeforeStart = logIsBefore(line, startTime)
    except:
      continue
    
  # go to next file if needed
  if (lineIndex >= len(logLines)):
    logFileIndex += 1
    if (logFileIndex >= len(logFiles)):
      return data
    logFileName = logFiles[logFileIndex]
    logFilePath = os.path.join(sensorFolderName, logFileName)

    with open(logFilePath, "r") as log:
      logStr = log.read()
    logLines = logStr.splitlines()
    lineIndex = 0
  line = logLines[lineIndex]

  isBeforeEnd = logIsBefore(line, endTime)
  while isBeforeEnd:
    try: # Adding line to data
      # using datatype to construct/cast the string from the logfile to the desired type
      data[DATA_MEASUREMENTS_FLAG].append(sensorType.datatype(removeSpaces(readFrom(line, sensorType.flag))))
      data[DATA_TIME_FLAG].append(convertStrToDatetime(line[0:DATETIME_STR_LENGTH]))
    except:
      if (keepErrors):
        data[DATA_MEASUREMENTS_FLAG].append(removeSpaces(readFrom(line, sensorType.flag)))
        data[DATA_TIME_FLAG].append(convertStrToDatetime(line[0:DATETIME_STR_LENGTH]))
      else:
        continue

    lineIndex += 1
    
    # go to the next file if needed
    if (lineIndex >= len(logLines)):
      logFileIndex += 1
      if (logFileIndex >= len(logFiles)):
        return data
      logFileName = logFiles[logFileIndex]
      logFilePath = os.path.join(sensorFolderName, logFileName)

      with open(logFilePath, "r") as log:
        logStr = log.read()
      logLines = logStr.splitlines()
      lineIndex = 0
    line = logLines[lineIndex]

    isBeforeEnd = logIsBefore(line, endTime)
    
  return data

# Gets the data for all sensors from the given start time to the endTime.
# startTime is inclusive, endTime is exclusive
def getDataByTimeAllSensors(glovebox: Glovebox, startTime: datetime.datetime, endTime: datetime.datetime, keepErrors=False):
  data = {}
  for sensor in glovebox.allSensors:
    data[sensor.flag] = getDataByTime(glovebox, startTime, endTime, sensor, keepErrors)
  return data

# -------------------- Plotting Data --------------------
# Plots certain data using matplotlib.
def plotData(data, plotFormat=None, title=None, xlabel=DATA_TIME_FLAG, ylabel=None):
  times = data[DATA_TIME_FLAG]
  measurements = data[DATA_MEASUREMENTS_FLAG]
  plt.title(title if title else flag)
  plt.xlabel(xlabel)
  plt.ylabel(ylabel if ylabel else flag)
  if (plotFormat):
    plt.plot(times, measurements, plotFormat)
  else:
    plt.plot(times, measurements)
# Plots certain data on a given subPlot using matplotlib.
def subPlotData(subPlot, data, plotFormat=None, title=None):
  times = data[DATA_TIME_FLAG]
  measurements = data[DATA_MEASUREMENTS_FLAG]
  subPlot.set_title(title if title else "untitled")
  if (plotFormat):
    subPlot.plot(times, measurements, plotFormat)
  else:
    subPlot.plot(times, measurements)

# -------------------- Analyzing and Manipulating Data --------------------

# TODO: reduce resolution

# -------------------- Manipulating Files --------------------