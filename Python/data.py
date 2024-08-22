# -------------------- File Description --------------------
# This is the file containing the data utilities for gems.
# These utilities can be used for analysis, plotting, etc.
# Right now, it expects the log files to be in glovebox-named folders,
# with those folders in the same directory as this script.

import gems
import matplotlib.pyplot as plt
from matplotlib import *
import os

# -------------------- Constants --------------------
DATA_TIME_FLAG = "Time"

# -------------------- Getting Data --------------------
# ---------- Data Format ----------
# getData methods will return a dictionary with a list of timestamps under the key DATA_TIME_FLAG,
# and a list of measurements under the key of the sensorType's flag. The timestamps correspond
# to the measurements in order (e.g. data[DATA_TIME_FLAG][2] is the timestamp for the data[sensorFlag][2])

# getAllData methods will return a dictionary with sub-dictionaries under the sensor flags as keys.
# The sub-dictionaries follow the same format as the data returned by getData methods.
# For example, to get the list of Temperature measurements, you could write data[gems.TEMP_FLAG][gems.TEMP_FLAG]

# For all data functions, the flag "keepErrors" decides whether or not to keep logs that can't be converted
# to the sensorType's datatype (e.g. "HIGH" and "LOW"). If true, they will be put into the data as raw strings.

# ---------- Data Utility Functions ----------
# gets data from the log file from and to the given lines
# startLine is inclusive and defaults to 0, endLine is exclusive and defaults to -1 which signifies the end of the file
def getDataByLines(logFile, sensorType, startLine=0, endLine=-1, keepErrors=False):
  data = {
    DATA_TIME_FLAG: [],
    sensorType.flag: []
  }
  if not os.path.exists(logFile):
    return data
    # raise FileNotFoundError("logFile does not exist")
  log = open(logFile, "r").read()
  logLines = log.splitlines()
  logLines = logLines[startLine:(endLine if endLine >= 0 else len(logLines))]
  for line in logLines:
    if not sensorType.flag in line: continue
    try:
      time = gems.convertStrToDatetime(line[0:gems.DATETIME_STR_LENGTH])
    except:
      continue
    try:
      # using datatype to construct/cast the string from the logfile to the desired type
      # If the flag is the last in the line, will just return everything after it
      data[sensorType.flag].append(sensorType.datatype(gems.removeSpaces(gems.readFromUntilFlags(line, sensorType.flag, gems.LOG_FLAGS))))
      data[DATA_TIME_FLAG].append(time)
    except:
      if (keepErrors):
        data[sensorType.flag].append(gems.removeSpaces(gems.readFromUntilFlags(line, sensorType.flag, gems.LOG_FLAGS)))
        data[DATA_TIME_FLAG].append(time)
      else:
        continue
      # raise TypeError("Invalid datatype when trying to getDataFromLineUntil. Flag: " + sensorType.flag + " Datatype: " + str(sensorType.datatype))
  return data
# gets the data for all sensors from the logfile. Needs a clean logfile with the format it expects.
# startLine is inclusive and defaults to 0, endLine is exclusive and defaults to -1 which signifies the end of the file
# logFile defaults to None, signifying the logFile for the current date
def getAllDataByLines(glovebox, logFile=None, startLine=0, endLine=-1, keepErrors=False):
  data = {
    DATA_TIME_FLAG: [],
  }
  for sensor in glovebox.allSensors:
    dictionary = {
      DATA_TIME_FLAG: [],
      sensor.flag: []
    }
    data[sensor.flag] = dictionary
  for sensor in glovebox.allSensors:
    data[sensor.flag] = []
  if not logFile:
    logFile = glovebox.getLogFileNameToday()
  if not os.path.exists(logFile):
    return data
    # raise FileNotFoundError("logFile does not exist")
  log = open(logFile, "r").read()
  logLines = log.splitlines()
  logLines = logLines[startLine:(endLine if endLine >= 0 else len(logLines))]
  for line in logLines:
    try:
      time = gems.convertStrToDatetime(line[0:gems.DATETIME_STR_LENGTH])
    except:
      continue
    for sensor in glovebox.allSensors:
      if not sensor.flag in line: continue
      try:
          # using datatype to construct/cast the string from the logfile to the desired type
          # If the flag is the last in the line, will just return everything after it
          data[sensor.flag][sensor.flag].append(sensor.datatype(gems.removeSpaces(gems.readFromUntilFlags(line, sensor.flag, gems.LOG_FLAGS))))
          data[sensor.flag][DATA_TIME_FLAG].append(time) # after in case of exception
      except:
        if (keepErrors):
          data[sensor.flag].append(gems.removeSpaces(gems.readFromUntilFlags(line, sensor.flag, gems.LOG_FLAGS)))
          data[DATA_TIME_FLAG].append(time)
        else:
          continue
          # raise TypeError("Invalid datatype when trying to getData. Flag: " + sensor.flag + " Datatype: " + str(sensor.datatype))
  return data
# get data from the last [numLines] number of lines
def getDataLastLines(logFile, numLines, sensorType, keepErrors=False):
  data = {
    DATA_TIME_FLAG: [],
    sensorType.flag: []
  }
  if not os.path.exists(logFile):
    return data
    # raise FileNotFoundError("logFile does not exist")
  log = open(logFile, "r").read()
  logLines = log.splitlines()
  logLines = logLines[len(logLines) - numLines:len(logLines)]
  for line in logLines:
    if not sensorType.flag in line: continue
    try:
      time = gems.convertStrToDatetime(line[0:gems.DATETIME_STR_LENGTH])
    except:
      continue
    try:
      # using datatype to construct/cast the string from the logfile to the desired type
      # If the flag is the last in the line, will just return everything after it
      data[sensorType.flag].append(sensorType.datatype(gems.removeSpaces(gems.readFromUntilFlags(line, sensorType.flag, gems.LOG_FLAGS))))
      data[DATA_TIME_FLAG].append(time)
    except:
      if (keepErrors):
        data[sensorType.flag].append(gems.removeSpaces(gems.readFromUntilFlags(line, sensorType.flag, gems.LOG_FLAGS)))
        data[DATA_TIME_FLAG].append(time)
      else:
        continue
      # raise TypeError("Invalid datatype when trying to getDataLastLines. Flag: " + sensorType.flag + " Datatype: " + str(sensorType.datatype))
  return data
# get data for all sensors from the last [numLines] number of lines
# logFile defaults to None, signifying the logFile for the current date
def getAllDataLastLines(glovebox, numLines, logFile=None, keepErrors=False):
  data = {
    DATA_TIME_FLAG: [],
  }
  for sensor in glovebox.allSensors:
    dictionary = {
      DATA_TIME_FLAG: [],
      sensor.flag: []
    }
    data[sensor.flag] = dictionary
  if not logFile:
    logFile = glovebox.getLogFileNameToday()
  if not os.path.exists(logFile):
    return data
    # raise FileNotFoundError("logFile does not exist")
  log = open(logFile, "r").read()
  logLines = log.splitlines()
  logLines = logLines[len(logLines) - numLines:len(logLines)]
  for line in logLines:
    try:
      time = gems.convertStrToDatetime(line[0:gems.DATETIME_STR_LENGTH])
    except:
      continue
    for sensor in glovebox.allSensors:
      if not sensor.flag in line: continue
      try:
          # using datatype to construct/cast the string from the logfile to the desired type
          # If the flag is the last in the line, will just return everything after it
          data[sensor.flag][sensor.flag].append(sensor.datatype(gems.removeSpaces(gems.readFromUntilFlags(line, sensor.flag, gems.LOG_FLAGS))))
          data[sensor.flag][DATA_TIME_FLAG].append(time) # after in case of exception
      except:
        if (keepErrors):
          data[sensor.flag].append(gems.removeSpaces(gems.readFromUntilFlags(line, sensor.flag, gems.LOG_FLAGS)))
          data[DATA_TIME_FLAG].append(time)
        else:
          continue
          # raise TypeError("Invalid datatype when trying to getData. Flag: " + sensor.flag + " Datatype: " + str(sensor.datatype))
  return data
# Gets data from the given start time to the endTime.
# startTime is inclusive, endTime is exclusive
def getDataByTime(glovebox, startTime, endTime, sensorType, keepErrors=False):
  if (endTime < startTime):
    raise ValueError("getDataByTime: endTime is before startTime")
  # initializing the structure for data
  data = {
    DATA_TIME_FLAG: [],
    sensorType.flag: []
  }
  # getting a list of the logFiles for the glovebox
  if not os.path.exists("./" + glovebox.name):
    return data # no data
  files = os.listdir("./" + glovebox.name)
  logFiles = []
  # Removing other files, like ErrorLog.txt, and empty files
  for file in files:
    if file[0:len(gems.LOG_FILE_PREFIX)] == gems.LOG_FILE_PREFIX and os.path.getsize("./" + glovebox.name + "/" + file):
      logFiles.append(file)
  logFiles.sort()

  # getting the right logFile to start at
  logFileName = gems.LOG_FILE_PREFIX + str(startTime)[0:10] + ".txt"
  logFilePath = "./" + glovebox.name + "/" + logFileName
  if not os.path.exists(logFilePath):
    # print("noExist")
    # Finding the next logFile that should be after this one
    logFilesWithFile = list(logFiles) # making a copy
    logFilesWithFile.append(logFileName)
    logFilesWithFile.sort()
    dirIndex = logFilesWithFile.index(logFileName)
    if (dirIndex < len(logFiles)):
      logFileName = logFiles[dirIndex]
      logFilePath = "./" + glovebox.name + "/" + logFileName
    else:
      return data
      #  raise FileNotFoundError("getDataByTime: No log files at or after start time. Glovebox: " + glovebox.name + " startTime: " + str(startTime))
  else:
    dirIndex = logFiles.index(logFileName)
  
  log = open(logFilePath, "r")
  logStr = log.read()
  log.close()
  logLines = logStr.splitlines()
  nextLineIndex = 0
  nextLine = logLines[0]

  # Looping through the lines until we get to lines we want to start adding to the data (i.e. lines after the startTime)
  isBefore = logIsBefore(nextLine, startTime) # so we can try/except in the loop
  while isBefore and nextLineIndex < len(logLines) - 1:
    nextLineIndex += 1
    nextLine = logLines[nextLineIndex]
    try:
      isBefore = logIsBefore(nextLine, startTime)
    except:
      continue
  
  # prevLine = None
  # prevLineIndex = None

  isBefore = logIsBefore(nextLine, endTime)
  while isBefore:
    prevLine = nextLine
    # prevLineIndex = nextLineIndex
    nextLineIndex += 1
    # go to the next file if needed
    if (nextLineIndex >= len(logLines)):
      dirIndex += 1
      # nonlocal logFiles
      if (dirIndex >= len(logFiles)):
        return data # No more files to parse
      logFileName = logFiles[dirIndex]
      logFilePath = "./" + glovebox.name + "/" + logFileName
      log = open(logFilePath, "r")
      logStr = log.read()
      log.close()
      logLines = logStr.splitlines()
      nextLineIndex = 0
    nextLine = logLines[nextLineIndex]
    # Safety checks
    if not sensorType.flag in prevLine: continue
    try:
      isBefore = logIsBefore(nextLine, endTime)
      time = gems.convertStrToDatetime(prevLine[0:gems.DATETIME_STR_LENGTH])
    except:
       continue
    # If all that is good...
    try:
      # using datatype to construct/cast the string from the logfile to the desired type
      # If the flag is the last in the line, will just return everything after it
      data[sensorType.flag].append(sensorType.datatype(gems.removeSpaces(gems.readFromUntilFlags(prevLine, sensorType.flag, gems.LOG_FLAGS))))
      data[DATA_TIME_FLAG].append(time)
    except:
      if (keepErrors):
        data[sensorType.flag].append(gems.removeSpaces(gems.readFromUntilFlags(prevLine, sensorType.flag, gems.LOG_FLAGS)))
        data[DATA_TIME_FLAG].append(time)
      else:
        continue
      # raise TypeError("Invalid datatype when trying to getDataByTime. Flag: " + sensorType.flag + " Line: " + str(prevLineIndex) + " Data: " +
      #    gems.removeSpaces(gems.readFromUntilFlags(prevLine, sensorType.flag, gems.LOG_FLAGS)) + " Datatype: " + str(sensorType.datatype))
    # nextLineIndex += 1
    
  return data
   # Gets data for all sensors from the given start time to the endTime.
# Gets the data for all sensors from the given start time to the endTime.
# startTime is inclusive, endTime is exclusive
def getAllDataByTime(glovebox, startTime, endTime, keepErrors=False):
  if (endTime < startTime):
    raise ValueError("getDataByTime: endTime is before startTime")
  # initializing the structure for data
  data = {
    DATA_TIME_FLAG: [],
  }
  for sensor in glovebox.allSensors:
    dictionary = {
      DATA_TIME_FLAG: [],
      sensor.flag: []
    }
    data[sensor.flag] = dictionary

  # getting a list of the logFiles for the glovebox
  if not os.path.exists("./" + glovebox.name):
    return data # no data
  files = os.listdir("./" + glovebox.name)
  logFiles = []
  # Removing other files, like ErrorLog.txt, and empty files
  for file in files:
    if file[0:len(gems.LOG_FILE_PREFIX)] == gems.LOG_FILE_PREFIX and os.path.getsize("./" + glovebox.name + "/" + file):
      logFiles.append(file)
  logFiles.sort()

  # getting the right logFile to start at
  logFileName = gems.LOG_FILE_PREFIX + str(startTime)[0:10] + ".txt"
  logFilePath = "./" + glovebox.name + "/" + logFileName
  if not os.path.exists(logFilePath):
    # Finding the next logFile that should be after this one
    logFilesWithFile = list(logFiles) # making a copy
    logFilesWithFile.append(logFileName)
    logFilesWithFile.sort()
    dirIndex = logFilesWithFile.index(logFileName)
    if (dirIndex < len(logFiles)):
      logFileName = logFiles[dirIndex]
      logFilePath = "./" + glovebox.name + "/" + logFileName
    else:
      return data
      # raise FileNotFoundError("getDataByTime: No log files at or after start time. Glovebox: " + glovebox.name + " startTime: " + str(startTime))
  else:
    dirIndex = logFiles.index(logFileName)
  
  log = open(logFilePath, "r")
  logStr = log.read()
  log.close()
  logLines = logStr.splitlines()
  nextLineIndex = 0
  nextLine = logLines[0]

  # Looping through the lines until we get to lines we want to start adding to the data (i.e. lines after the startTime)
  isBefore = logIsBefore(nextLine, startTime) # so we can try/except in the loop
  while isBefore and nextLineIndex < len(logLines) - 1:
    nextLineIndex += 1
    nextLine = logLines[nextLineIndex]
    try:
      isBefore = logIsBefore(nextLine, startTime)
    except:
      continue # (i.e. do nothing)

  isBefore = logIsBefore(nextLine, endTime)
  while isBefore:
    prevLine = nextLine
    nextLineIndex += 1
    # go to the next file if needed
    if (nextLineIndex >= len(logLines)):
      dirIndex += 1
      if (dirIndex >= len(logFiles)):
        return data # No more files to parse
      logFileName = logFiles[dirIndex]
      logFilePath = "./" + glovebox.name + "/" + logFileName
      log = open(logFilePath, "r")
      logStr = log.read()
      log.close()
      logLines = logStr.splitlines()
      nextLineIndex = 0
    nextLine = logLines[nextLineIndex]
    # Safety checks
    try:
      isBefore = logIsBefore(nextLine, endTime)
      time = gems.convertStrToDatetime(prevLine[0:gems.DATETIME_STR_LENGTH])
    except:
      continue
    for sensor in glovebox.allSensors:
      if not sensor.flag in prevLine: continue
      try:
        # using the corresponding datatype to construct/cast the string from the logfile to the desired type
        # If the flag is the last in the line, will just return everything after it
        data[sensor.flag][sensor.flag].append(sensor.datatype(gems.removeSpaces(gems.readFromUntilFlags(prevLine, sensor.flag, gems.LOG_FLAGS))))
        data[sensor.flag][DATA_TIME_FLAG].append(time) # goes after in case of exception
      except:
        if (keepErrors):
          data[sensor.flag][sensor.flag].append(gems.removeSpaces(gems.readFromUntilFlags(prevLine, sensor.flag, gems.LOG_FLAGS)))
          data[sensor.flag][DATA_TIME_FLAG].append(time) # goes after in case of exception
        else:
          continue
        # raise TypeError("Invalid datatype when trying to getDataByTime. Flag: " + sensor.flag + " Line: " + str(prevLineIndex) + " Data: " +
        #     gems.removeSpaces(gems.readFromUntilFlags(prevLine, sensor.flag, gems.LOG_FLAGS)) + " Datatype: " + str(sensor.datatype))
  return data

def getLastMeasurement(glovebox, sensorType, keepErrors=False):
  data = {
    DATA_TIME_FLAG: None,
    sensorType.flag: None
  }
  # getting a list of the logFiles for the glovebox
  if not os.path.exists("./" + glovebox.name):
    return data # no data
  files = os.listdir("./" + glovebox.name)
  logFiles = []
  # Removing other files, like ErrorLog.txt, and empty files
  for file in files:
    if file[0:len(gems.LOG_FILE_PREFIX)] == gems.LOG_FILE_PREFIX and os.path.getsize("./" + glovebox.name + "/" + file):
      logFiles.append(file)
  logFiles.sort()

  dirIndex = len(logFiles) - 1 # since they're sorted chronologically
  
  logFileName = logFiles[dirIndex]
  logFilePath = "./" + glovebox.name + "/" + logFileName
  log = open(logFilePath, "r")
  logStr = log.read()
  log.close()
  logLines = logStr.splitlines()
  lineIndex = len(logLines)

  while not data[DATA_TIME_FLAG]: # i.e. while we haven't gotten the data
    lineIndex -= 1
    if lineIndex <= 0:
      dirIndex -= 1
      if dirIndex <= 0:
        return data # no data found
      logFileName = logFiles[dirIndex]
      logFilePath = "./" + glovebox.name + "/" + logFileName
      log = open(logFilePath, "r")
      logStr = log.read()
      log.close()
      logLines = logStr.splitlines()
      lineIndex = len(logLines) - 1
    line = logLines[lineIndex]
    if not sensorType.flag in line: continue
    try:
      time = gems.convertStrToDatetime(line[0:gems.DATETIME_STR_LENGTH])
    except:
       continue
    try:
      # using datatype to construct/cast the string from the logfile to the desired type
      # If the flag is the last in the line, will just return everything after it
      data[sensorType.flag] = sensorType.datatype(gems.removeSpaces(gems.readFromUntilFlags(line, sensorType.flag, gems.LOG_FLAGS)))
      data[DATA_TIME_FLAG] = time
    except:
      if (keepErrors):
        data[sensorType.flag] = gems.removeSpaces(gems.readFromUntilFlags(line, sensorType.flag, gems.LOG_FLAGS))
        data[DATA_TIME_FLAG] = time
      else:
        continue
  return data

def getAllLastMeasurements(glovebox, keepErrors=False):
  data = {}
  for sensor in glovebox.allSensors:
    data[sensor.flag] = {
      DATA_TIME_FLAG: None,
      sensor.flag: None
    }
  # getting a list of the logFiles for the glovebox
  if not os.path.exists("./" + glovebox.name):
    return data # no data
  files = os.listdir("./" + glovebox.name)
  logFiles = []
  # Removing other files, like ErrorLog.txt, and empty files
  for file in files:
    if file[0:len(gems.LOG_FILE_PREFIX)] == gems.LOG_FILE_PREFIX and os.path.getsize("./" + glovebox.name + "/" + file):
      logFiles.append(file)
  logFiles.sort()

  dirIndex = len(logFiles) - 1 # since they're sorted chronologically
  
  logFileName = logFiles[dirIndex]
  logFilePath = "./" + glovebox.name + "/" + logFileName
  log = open(logFilePath, "r")
  logStr = log.read()
  log.close()
  logLines = logStr.splitlines()
  lineIndex = len(logLines)

  hasAllData = False

  while not hasAllData: # i.e. while we haven't gotten the data
    lineIndex -= 1
    if lineIndex < 0:
      dirIndex -= 1
      if dirIndex < 0:
        return data # limited or no data found
      logFileName = logFiles[dirIndex]
      logFilePath = "./" + glovebox.name + "/" + logFileName
      log = open(logFilePath, "r")
      # print(logFileName)
      logStr = log.read()
      log.close()
      logLines = logStr.splitlines()
      lineIndex = len(logLines) - 1
    line = logLines[lineIndex]
    for sensor in glovebox.allSensors:
      if not sensor.flag in line:
        continue
      if data[sensor.flag][DATA_TIME_FLAG]:
        continue
      try:
        time = gems.convertStrToDatetime(line[0:gems.DATETIME_STR_LENGTH])
        # print(line[0:gems.DATETIME_STR_LENGTH])
      except:
        continue
      try:
        # using datatype to construct/cast the string from the logfile to the desired type
        # If the flag is the last in the line, will just return everything after it
        data[sensor.flag][sensor.flag] = sensor.datatype(gems.removeSpaces(gems.readFromUntilFlags(line, sensor.flag, gems.LOG_FLAGS)))
        data[sensor.flag][DATA_TIME_FLAG] = time
      except:
        if (keepErrors):
          data[sensor.flag][sensor.flag] = gems.removeSpaces(gems.readFromUntilFlags(line, sensor.flag, gems.LOG_FLAGS))
          data[sensor.flag][DATA_TIME_FLAG] = time
        else:
          continue
    hasAllData = True
    for sensor in glovebox.allSensors:
      if not data[sensor.flag][DATA_TIME_FLAG]:
        hasAllData = False
  # print(errs)
  return data

# -------------------- Plotting Data --------------------
# Plots certain data using matplotlib.
def plotData(data, flag, plotFormat=None, title=None, xlabel=DATA_TIME_FLAG, ylabel=None):
  times = data[DATA_TIME_FLAG]
  flagData = data[flag]
  plt.title(title if title else flag)
  plt.xlabel(xlabel)
  plt.ylabel(ylabel if ylabel else flag)
  if (plotFormat):
    plt.plot(times, flagData, plotFormat)
  else:
    plt.plot(times, flagData)
# Plots certain data on a given subPlot using matplotlib.
def subPlotData(subPlot, data, flag, plotFormat=None, title=None):
  times = data[DATA_TIME_FLAG]
  flagData = data[flag]
  subPlot.set_title(title if title else flag)
  if (plotFormat):
    subPlot.plot(times, flagData, plotFormat)
  else:
    subPlot.plot(times, flagData)

# -------------------- Internal Utilities --------------------
def logIsBefore(line, time):
  return gems.convertStrToDatetime(line[0:gems.DATETIME_STR_LENGTH]) < time
