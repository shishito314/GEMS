"""
Description:
----------
Data utilities for analysis, plotting, etc. with glovebox data.
Expects log files to be at ./glovebox/sensor/
with glovebox being the glovebox name and sensor being the sensor type.

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
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from typing import Union
import datetime
import os

from gems import *

# -------------------- Constants --------------------
DATA_TIME_KEY = "Time"
DATA_MEASUREMENT_KEY = "Data"
DATA_ERROR_KEY = "Error"

# ---------- Data Utility Functions ----------
def getLastNMeasurements(glovebox: Glovebox, sensorType: Union[Sensor, type[Sensor]], numEntries: int, keepErrors=False) -> Dict[str, List]:
    """Gets data from the last [numEntries] entries"""
    data = {DATA_TIME_KEY: [], DATA_MEASUREMENT_KEY: []}

    sensorFolder = glovebox.getSensorFolderPath(sensorType)
    if not os.path.isdir(sensorFolder):
        return data
    logFiles = sorted(
        [f for f in os.listdir(sensorFolder) if isLogFile(f)], reverse=True
    )

    for logFileName in logFiles:
        logFileDate = getDateFromLogFileName(logFileName)
        with open(os.path.join(sensorFolder, logFileName)) as log:
            lines = reversed(log.readlines())
        for line in lines:
            try:
                dateTime = datetime.datetime.combine(
                    logFileDate, getTimeFromLogLine(line)
                )
                rawStr = removeSpaces(readFrom(line, " "))
                try:
                    measurement = sensorType.datatype(rawStr)
                except:
                    if not keepErrors:
                        continue
                    measurement = rawStr

                data[DATA_TIME_KEY].append(dateTime)
                data[DATA_MEASUREMENT_KEY].append(measurement)
            except:
                continue
            if len(data[DATA_TIME_KEY]) >= numEntries:
                return data

    return data

def getLastNMeasurementsAllSensors(glovebox: Glovebox, numEntries: int, keepErrors=False) -> Dict[str, Dict[str, List]]:
    """get data for all sensors from the last [numEntries] entries. logFile defaults to None, signifying the logFile for the current date"""
    data = {}
    for sensor in glovebox.allSensors:
        data[sensor.flag] = getLastNMeasurements(
            glovebox, numEntries, sensor, keepErrors
        )
    return data

def getLastMeasurement(glovebox: Glovebox, sensorType: Union[Sensor, type[Sensor]], keepErrors=False) -> Dict[str, Any]:
    """Gets the last measurement taken for the given glovebox and sensor."""
    data = {DATA_TIME_KEY: None, DATA_MEASUREMENT_KEY: None}

    sensorFolder = glovebox.getSensorFolderPath(sensorType)
    if not os.path.isdir(sensorFolder):
        return data
    logFiles = sorted(
        [f for f in os.listdir(sensorFolder) if isLogFile(f)], reverse=True
    )

    for logFileName in logFiles:
        logFileDate = getDateFromLogFileName(logFileName)
        with open(os.path.join(sensorFolder, logFileName)) as log:
            lines = reversed(log.readlines())
        for line in lines:
            try:
                dateTime = datetime.datetime.combine(
                    logFileDate, getTimeFromLogLine(line)
                )
                rawStr = removeSpaces(readFrom(line, " "))
                try:
                    measurement = sensorType.datatype(rawStr)
                except:
                    if not keepErrors:
                        continue
                    measurement = rawStr

                data[DATA_TIME_KEY] = dateTime
                data[DATA_MEASUREMENT_KEY] = measurement
                return data
            except:
                continue

    return data

def getLastMeasurementAllSensors(glovebox: Glovebox, keepErrors=False) -> Dict[str, Dict[str, Any]]:
    data = {}
    for sensor in glovebox.allSensors:
        data[sensor.flag] = getLastMeasurement(glovebox, sensor, keepErrors)
    return data

def getDataByTime(glovebox: Glovebox, sensorType: Union[Sensor, type[Sensor]], startTime: datetime.datetime, endTime: datetime.datetime, keepErrors=False) -> Dict[str, List]:
    """Gets data from the given start time to the endTime. startTime is inclusive, endTime is exclusive."""
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
        logFileDate = getDateFromLogFileName(logFileName)
        with open(os.path.join(sensorFolder, logFileName)) as log:
            for line in log:
                try:
                    dateTime = datetime.datetime.combine(
                        logFileDate, getTimeFromLogLine(line)
                    )
                    if dateTime < startTime:
                        continue
                    if dateTime >= endTime:
                        return data

                    rawStr = removeSpaces(readFrom(line, " "))
                    try:
                        measurement = sensorType.datatype(rawStr)
                    except:
                        if not keepErrors:
                            continue
                        measurement = rawStr

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

def getErrorsByTime(glovebox: Glovebox, sensorType: Union[Sensor, type[Sensor]], startTime: datetime.datetime, endTime: datetime.datetime) -> Dict[str, List[Union[datetime.datetime, str]]]:
    """Gets errors from the given start time to the endTime. startTime is inclusive, endTime is exclusive"""
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
        errorFileDate = getDateFromErrorFileName(errorFileName)
        with open(os.path.join(errorFolder, errorFileName)) as log:
            for line in log:
                try:
                    dateTime = datetime.datetime.combine(
                        errorFileDate, getTimeFromLogLine(line)
                    )
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
        errorFileDate = getDateFromErrorFileName(errorFileName)
        with open(os.path.join(errorFolder, errorFileName)) as log:
            for line in log:
                try:
                    dateTime = datetime.datetime.combine(
                        errorFileDate, getTimeFromLogLine(line)
                    )
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
    times = data[DATA_TIME_KEY]
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
    times = data[DATA_TIME_KEY]
    measurements = data[DATA_MEASUREMENT_KEY]
    subPlot.set_title(title if title else "untitled")
    if plotFormat:
        subPlot.plot(times, measurements, plotFormat)
    else:
        subPlot.plot(times, measurements)

def subPlotErrors(subPlot: Axes, errors, **plotFormat):
    """Plots given errors on a given sub-plot using matplotlib."""
    times = errors[DATA_TIME_KEY]
    if plotFormat:
        for time in times:
            subPlot.axvline(time, **plotFormat)
    else:
        for time in times:
            subPlot.axvline(time, **plotFormat)
