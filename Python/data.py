"""
Description:
----------
Data utilities for analysis, plotting, etc. with glovebox data.
Expects log files to be at ./glovebox/sensor/
with glovebox being the glovebox name and sensor being the sensor type.

Times:
----------
All the timestamps returned by the data parsing functions will be in UTC time.
They can be converted to the local time using the astimezone() function from the datetime module,
for example as follows:

times = [t.astimezone() for t in data[DATA_TIME_KEY]]

The data functions that take datetime arguments can be given any timezone, as the arguments will
be converted to UTC time internally.

Data Format:
----------
Functions that get a specific sensor's data will return a dictionary with a list of timestamps
under the key DATA_TIME_KEY, and a list of measurements under the key of DATA_MEASUREMENT_KEY.
The timestamps correspond to the measurements in order
(e.g. data[DATA_TIME_KEY][2] is the timestamp for the data[DATA_MEASUREMENT_KEY][2])

Functions that get data for all sensors will return a dictionary with sub-dictionaries under the sensor flags as keys.
The sub-dictionaries follow the same format as the data returned by the single-sensor functions
For example, to get the list of Temperature measurements, you could write data[TEMP_FLAG][DATA_MEASUREMENT_KEY]

For all data functions, the flag "keepErrors" decides whether or not to keep logs that can't be converted
to the sensorType's datatype (e.g. "HIGH" and "LOW"). If true, they will be put into the data as raw strings.
"""
import datetime
import os
from typing import Any, Type, Union

import matplotlib.pyplot as plt
from gems import *
from matplotlib.axes import Axes

# -------------------- Constants --------------------
DATA_TIME_KEY = "Time"
DATA_MEASUREMENT_KEY = "Data"
DATA_ERROR_KEY = "Error"

# ---------- Data Utility Functions ----------
def parseLine(line, sensorType, keepErrors) -> tuple[datetime.datetime, Any]:
    """Gets the time and measurement from a single line of a log file"""
    dateTime = getDateTimeFromLogLine(line)
    rawStr = readFrom(line, " : ")
    try:
        measurement = sensorType.datatype(rawStr)
    except:
        if not keepErrors:
            raise ValueError(f"Could not convert \"{rawStr}\" to type {sensorType.datatype}")
        measurement = rawStr

    return dateTime, measurement

def getRecentData(glovebox: Glovebox, sensorType: Union[Sensor, Type[Sensor]], numEntries: int, keepErrors=False) -> Dict[str, List]:
    """Gets data from the last [numEntries] entries"""
    data = {DATA_TIME_KEY: [], DATA_MEASUREMENT_KEY: []}

    sensorFolder = glovebox.getSensorFolderPath(sensorType)
    if not os.path.isdir(sensorFolder):
        return data
    logFiles = sorted(
        [f for f in os.listdir(sensorFolder) if isLogFile(f)], reverse=True
    )

    for logFileName in logFiles:
        # logFileDate = getDateFromLogFileName(logFileName)
        with open(os.path.join(sensorFolder, logFileName)) as log:
            lines = reversed(log.readlines())
        for line in lines:
            try:
                dateTime, measurement = parseLine(line, sensorType, keepErrors)

                data[DATA_TIME_KEY].append(dateTime)
                data[DATA_MEASUREMENT_KEY].append(measurement)
            except:
                continue
            if len(data[DATA_TIME_KEY]) >= numEntries:
                return data

    return data

def getRecentDataAllSensors(glovebox: Glovebox, numEntries: int, keepErrors=False) -> Dict[str, Dict[str, List]]:
    """get data for all sensors from the last [numEntries] entries"""
    data = {}
    for sensor in glovebox.allSensors:
        data[sensor.flag] = getRecentData(
            glovebox, numEntries, sensor, keepErrors
        )
    return data

def getDataByTime(glovebox: Glovebox, sensorType: Union[Sensor, Type[Sensor]], startTime: datetime.datetime, endTime: datetime.datetime, keepErrors=False) -> Dict[str, List]:
    """Gets data from the given start time to the endTime. startTime is inclusive, endTime is exclusive."""
    startTime = startTime.astimezone(datetime.timezone.utc)
    endTime = endTime.astimezone(datetime.timezone.utc)
    if endTime < startTime:
        raise ValueError("getDataByTime: endTime is before startTime")

    data = {DATA_TIME_KEY: [], DATA_MEASUREMENT_KEY: []}

    sensorFolder = glovebox.getSensorFolderPath(sensorType)
    if not os.path.isdir(sensorFolder):
        return data
    logFiles = sorted(
        [
            f
            for f in os.listdir(sensorFolder)
            if isLogFile(f) and getDateFromLogFileName(f) >= startTime.date()
        ]
    )

    for logFileName in logFiles:
        # logFileDate = getDateFromLogFileName(logFileName)
        with open(os.path.join(sensorFolder, logFileName)) as log:
            for line in log:
                try:
                    dateTime, measurement = parseLine(line, sensorType, keepErrors)

                    if dateTime < startTime:
                        continue
                    if dateTime >= endTime:
                        return data

                    data[DATA_TIME_KEY].append(dateTime)
                    data[DATA_MEASUREMENT_KEY].append(measurement)

                except:
                    continue

    return data

def getDataByTimeAllSensors(glovebox: Glovebox, startTime: datetime.datetime, endTime: datetime.datetime, keepErrors=False,) -> Dict[str, Dict[str, List]]:
    """Gets the data for all sensors from the given start time to the endTime. startTime is inclusive, endTime is exclusive."""
    data = {}
    for sensor in glovebox.allSensors:
        data[sensor.flag] = getDataByTime(
            glovebox, startTime, endTime, sensor, keepErrors
        )
    return data

def getLastMeasurement(glovebox: Glovebox, sensorType: Union[Sensor, Type[Sensor]], keepErrors=False) -> Dict[str, Any]:
    """Gets the last measurement taken for the given glovebox and sensor."""
    data = {DATA_TIME_KEY: None, DATA_MEASUREMENT_KEY: None}

    sensorFolder = glovebox.getSensorFolderPath(sensorType)
    if not os.path.isdir(sensorFolder):
        return data
    logFiles = sorted(
        [f for f in os.listdir(sensorFolder) if isLogFile(f)], reverse=True
    )

    for logFileName in logFiles:
        # logFileDate = getDateFromLogFileName(logFileName)
        with open(os.path.join(sensorFolder, logFileName)) as log:
            lines = reversed(log.readlines())
        for line in lines:
            try:
                dateTime, measurement = parseLine(line, sensorType, keepErrors)

                data[DATA_TIME_KEY] = dateTime
                data[DATA_MEASUREMENT_KEY] = measurement
                return data
            except:
                continue

    return data

def getLastMeasurementAllSensors(glovebox: Glovebox, keepErrors=False) -> Dict[str, Dict[str, Any]]:
    """Gets the last measurement taken for the given glovebox and all sensors."""
    data = {}
    for sensor in glovebox.allSensors:
        data[sensor.flag] = getLastMeasurement(glovebox, sensor, keepErrors)
    return data

def getMeasurementNearTime(glovebox: Glovebox, sensorType: Union[Sensor, Type[Sensor]], dateTime: datetime.datetime, keepErrors=False) -> Dict[str, Any]:
    """Gets the measurement taken closest to the given time for the given glovebox and sensor."""
    dateTime = dateTime.astimezone(datetime.timezone.utc)
    
    def searchForEntry(lines, reverse: bool) -> tuple[datetime.time, Any, int]:
        entryTime = None
        entryMeasurement = None
        if reverse:
            lines = reversed(lines)
        for line in lines:
            try:
                entryTime, entryMeasurement = parseLine(line, sensorType, keepErrors)
                break
            except:
                pass
        return entryTime, entryMeasurement
    
    def searchNeighborFile(dateTime, sensorFolder, logFiles, fileIndex, isBefore):
        newFileMeasurement = None
        newFileDatetime = None
        offset = None
        while not (newFileDatetime and newFileMeasurement != None) and 0 <= fileIndex < len(logFiles):
            with open(os.path.join(sensorFolder, logFiles[fileIndex])) as log:
                lines = log.readlines()
            newFileDatetime, newFileMeasurement = searchForEntry(lines, True) if isBefore else searchForEntry(lines, False)
            fileIndex += -1 if isBefore else 1
        fileIndex += 1 if isBefore else -1
        if 0 <= fileIndex < len(logFiles) and newFileDatetime:
            offset = dateTime - newFileDatetime
        return offset, newFileDatetime, newFileMeasurement

    def getNearestEntryFromNeighborFiles(dateTime, sensorFolder, logFiles, prevIndex, nextIndex):
        data = {DATA_TIME_KEY: None, DATA_MEASUREMENT_KEY: None}
        beforeOffset, prevFileLastDatetime, prevFileLastMeasurement = searchNeighborFile(dateTime, sensorFolder, logFiles, prevIndex, True)
        afterOffset, nextFileFirstDatetime, nextFileFirstMeasurement = searchNeighborFile(dateTime, sensorFolder, logFiles, nextIndex, False)

        if beforeOffset and afterOffset:
            if abs(beforeOffset) < abs(afterOffset):
                data[DATA_TIME_KEY] = prevFileLastDatetime
                data[DATA_MEASUREMENT_KEY] = prevFileLastMeasurement
            else:
                data[DATA_TIME_KEY] = nextFileFirstDatetime
                data[DATA_MEASUREMENT_KEY] = nextFileFirstMeasurement
        elif beforeOffset:
            data[DATA_TIME_KEY] = prevFileLastDatetime
            data[DATA_MEASUREMENT_KEY] = prevFileLastMeasurement
        elif afterOffset:
            data[DATA_TIME_KEY] = nextFileFirstDatetime
            data[DATA_MEASUREMENT_KEY] = nextFileFirstMeasurement
        return data

    data = {DATA_TIME_KEY: None, DATA_MEASUREMENT_KEY: None}

    sensorFolder = glovebox.getSensorFolderPath(sensorType)
    if not os.path.isdir(sensorFolder):
        return data
    logFiles = sorted(
        [f for f in os.listdir(sensorFolder) if isLogFile(f)]
    )

    logFileForTime = os.path.basename(glovebox.getLogFilePathWithDateTime(dateTime, sensorType))
    if logFileForTime in logFiles:
        logFileName = logFileForTime
        with open(os.path.join(sensorFolder, logFileName)) as log:
            lines = log.readlines()

        firstDateTime, firstMeasurement = searchForEntry(lines, False)
        lastDateTime, lastMeasurement = searchForEntry(lines, True)

        if not (firstDateTime and firstMeasurement != None):
            prevIndex = logFiles.index(logFileName) - 1
            nextIndex = logFiles.index(logFileName) + 1
            return getNearestEntryFromNeighborFiles(dateTime, sensorFolder, logFiles, prevIndex, nextIndex)

        if firstDateTime > dateTime:
            prevIndex = logFiles.index(logFileName) - 1
            if prevIndex >= 0:
                with open(os.path.join(sensorFolder, logFiles[prevIndex])) as log:
                    prevFileLines = log.readlines()
                timeOffset = firstDateTime - dateTime
                prevFileLastDatetime, prevFileLastMeasurement = searchForEntry(prevFileLines, True)
                if prevFileLastDatetime and prevFileLastMeasurement != None:
                    if dateTime - prevFileLastDatetime < timeOffset:
                        data[DATA_TIME_KEY] = prevFileLastDatetime
                        data[DATA_MEASUREMENT_KEY] = prevFileLastMeasurement
                        return data
            data[DATA_TIME_KEY] = firstDateTime #datetime.datetime.combine(logFileDate, firstTime)
            data[DATA_MEASUREMENT_KEY] = firstMeasurement
            return data

        elif lastDateTime < dateTime:
            nextIndex = logFiles.index(logFileName) + 1
            if nextIndex < len(logFiles):
                with open(os.path.join(sensorFolder, logFiles[nextIndex])) as log:
                    nextFileLines = log.readlines()
                timeOffset = dateTime - lastDateTime
                nextFileFirstDateTime, nextFileFirstMeasurement = searchForEntry(nextFileLines, False)
                if nextFileFirstDateTime and nextFileFirstMeasurement != None:
                    if nextFileFirstDateTime - dateTime <= timeOffset:
                        data[DATA_TIME_KEY] = nextFileFirstDateTime
                        data[DATA_MEASUREMENT_KEY] = nextFileFirstMeasurement
                        return data
            data[DATA_TIME_KEY] = lastDateTime #datetime.datetime.combine(logFileDate, lastTime)
            data[DATA_MEASUREMENT_KEY] = lastMeasurement
            return data
            
        else:
            # not doing binary search because of malformed line risk
            minimumOffset = datetime.timedelta(days=1, hours=1) # 25 hours
            closestDateTime = None
            closestTimeMeasurement = None
            for line in lines:
                try:
                    lineTime, measurement = parseLine(line, sensorType, keepErrors)
                except:
                    continue
                offset = abs(lineTime - dateTime)
                if offset > minimumOffset: # passed the closest element
                    break
                minimumOffset = offset
                closestDateTime = lineTime
                closestTimeMeasurement = measurement
            
            if not closestDateTime:
                prevIndex = logFiles.index(logFileName) - 1
                nextIndex = logFiles.index(logFileName) + 1
                return getNearestEntryFromNeighborFiles(dateTime, sensorFolder, logFiles, prevIndex, nextIndex)

            data[DATA_TIME_KEY] = closestDateTime
            data[DATA_MEASUREMENT_KEY] = closestTimeMeasurement
            return data
        
    else:
        nextIndex = 0
        for i in range(0,len(logFiles) + 1):
            nextIndex = i
            if nextIndex < len(logFiles) and getDateFromLogFileName(logFiles[i]) > dateTime.date():
                break
        prevIndex = nextIndex - 1
        return getNearestEntryFromNeighborFiles(dateTime, sensorFolder, logFiles, prevIndex, nextIndex)
        
def getMeasurementNearTimeAllSensors(glovebox: Glovebox, dateTime: datetime.datetime, keepErrors=False) -> Dict[str, Dict[str, Any]]:
    data = {}
    for sensor in glovebox.allSensors:
        data[sensor.flag] = getMeasurementNearTime(glovebox, sensor, dateTime, keepErrors)
    return data

def getErrorsByTime(glovebox: Glovebox, sensorType: Union[Sensor, Type[Sensor]], startTime: datetime.datetime, endTime: datetime.datetime) -> Dict[str, List[Union[datetime.datetime, str]]]:
    """Gets errors from the given start time to the endTime. startTime is inclusive, endTime is exclusive"""
    startTime = startTime.astimezone(datetime.timezone.utc)
    endTime = endTime.astimezone(datetime.timezone.utc)
    if endTime < startTime:
        raise ValueError("getDataByTime: endTime is before startTime")

    errors = {DATA_TIME_KEY: [], DATA_ERROR_KEY: []}

    errorFolder = glovebox.getErrorFolderPath()
    if not os.path.isdir(errorFolder):
        return errors
    errorFiles = sorted(
        [
            f
            for f in os.listdir(errorFolder)
            if isErrorFile(f) and getDateFromErrorFileName(f) >= startTime.date()
        ]
    )

    for errorFileName in errorFiles:
        # errorFileDate = getDateFromErrorFileName(errorFileName)
        with open(os.path.join(errorFolder, errorFileName)) as log:
            for line in log:
                try:
                    dateTime = getDateTimeFromLogLine(line)
                    if dateTime < startTime:
                        continue
                    if dateTime >= endTime:
                        return errors

                    errorMssg = readFrom(line, "]").strip()

                    sensorStr = readFromUntilRequireEnd(line, "[", "]").split()
                    if (
                        sensorType.__class__.__name__
                        if isinstance(sensorType, Sensor)
                        else sensorType.__name__
                    ) in sensorStr:
                        errors[DATA_TIME_KEY].append(dateTime)
                        errors[DATA_ERROR_KEY].append(errorMssg)

                except:
                    continue

    return errors

def getErrorsByTimeAllSensors(glovebox: Glovebox, startTime: datetime.datetime, endTime: datetime.datetime) -> Dict[str, List[Union[datetime.datetime, str]]]:
    """Gets errors for all sensors from the given start time to the endTime. startTime is inclusive, endTime is exclusive"""
    if endTime < startTime:
        raise ValueError("getDataByTime: endTime is before startTime")

    errors = {}

    for sensor in glovebox.allSensors:
        errors[sensor.flag] = {DATA_TIME_KEY: [], DATA_ERROR_KEY: []}

    errorFolder = glovebox.getErrorFolderPath()
    if not os.path.isdir(errorFolder):
        return errors
    errorFiles = sorted(
        [
            f
            for f in os.listdir(errorFolder)
            if isErrorFile(f) and getDateFromErrorFileName(f) >= startTime.date()
        ]
    )

    for errorFileName in errorFiles:
        # errorFileDate = getDateFromErrorFileName(errorFileName)
        with open(os.path.join(errorFolder, errorFileName)) as log:
            for line in log:
                try:
                    dateTime = getDateTimeFromLogLine(line)
                    if dateTime < startTime:
                        continue
                    if dateTime >= endTime:
                        return errors

                    errorMssg = readFrom(line, "]").strip()

                    sensorStr = readFromUntilRequireEnd(line, "[", "]").split()
                    for sensor in glovebox.allSensors:
                        if sensor.__class__.__name__ in sensorStr:
                            errors[DATA_TIME_KEY].append(dateTime)
                            errors[DATA_ERROR_KEY].append(errorMssg)

                except:
                    continue

    return errors

# -------------------- Plotting Data --------------------
def plotData(data: Dict[str, List], plotFormat=None, title=None, xlabel=DATA_TIME_KEY, ylabel=None):
    """Plots given data using matplotlib."""
    times = [t.astimezone() for t in data[DATA_TIME_KEY]]
    measurements = data[DATA_MEASUREMENT_KEY]
    plt.title(title if title else flag)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel if ylabel else flag)
    if plotFormat:
        plt.plot(times, measurements, plotFormat)
    else:
        plt.plot(times, measurements)

def subPlotData(subPlot: Axes, data: Dict[str, List], plotFormat=None, title=None):
    """Plots given data on a given sub-plot using matplotlib."""
    times = [t.astimezone() for t in data[DATA_TIME_KEY]]
    measurements = data[DATA_MEASUREMENT_KEY]
    subPlot.set_title(title if title else "untitled")
    if plotFormat:
        subPlot.plot(times, measurements, plotFormat)
    else:
        subPlot.plot(times, measurements)

def subPlotErrors(subPlot: Axes, errors, **plotFormat):
    """Plots given errors on a given sub-plot using matplotlib."""
    times = [t.astimezone() for t in errors[DATA_TIME_KEY]]
    if plotFormat:
        for time in times:
            subPlot.axvline(time, **plotFormat)
    else:
        for time in times:
            subPlot.axvline(time, **plotFormat)

# -------------------- Misc --------------------
def verifyFile(filePath, sensorType: Union[Sensor, Type[Sensor]], keepErrors=False) -> bool:
    """Verify that the given file can be parsed for data."""
    if not os.path.exists(filePath):
        raise ValueError("Invalid file path")
    # logFileDate = getDateFromLogFileName(os.path.basename(filePath))
    lastDateTime = datetime.datetime.min
    with open(filePath) as log:
        for line in log:
            try:
                dateTime = getDateTimeFromLogLine(line)
                if dateTime < lastDateTime:
                    return False

                rawStr = removeSpaces(readFrom(line, " "))
                try:
                    _ = sensorType.datatype(rawStr)
                except:
                    if not keepErrors:
                        return False

            except:
                return False
    return True