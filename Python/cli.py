# -------------------- File Description --------------------
# This file contains code for a simple CLI (Command Line Interface)
# to interact with the GEMS system. Functionality may be added
# as needed or desired

import gems
import data

# Functions
def printHelp(_):
  print("Here are the possible commands:")
  print("    close - stop this CLI")
  print()
  print("  Get Data:")
  print("    latest - get latest measurements")
  print()
  print("  Manipulate Files")
  print("    clear_err <glovebox> - clear the errorLog for the given glovebox")

def printCurrent(_):
  print("Last successful logs:")
  for glovebox in gems.gloveboxes:
    print(glovebox.name)
    currentData = data.getLastMeasurementAllSensors(glovebox)
    for sensor in glovebox.allSensors:
      print(sensor.flag, end="\t")
      print(gems.getDatetimeStr(currentData[sensor.flag][data.DATA_TIME_FLAG]) if not currentData[sensor.flag][data.DATA_TIME_FLAG] == None else "_____", end="\t")
      print(gems.getDatetimeStr(currentData[sensor.flag][sensor.flag]) if not currentData[sensor.flag][sensor.flag] == None else "_____")

def clearErr(args):
  if len(args) != 1:
    print("Enter exactly one argument after \"clear_err\", the glovebox whose error log you would like to clear")
    return
  with open(gems.getGloveboxByName(args[0]).getErrorLogPath(), "w") as errorFile:
    errorFile.truncate(0)

inputFunctionTuples = [
  ("help", printHelp),
  ("latest", printCurrent),
  ("clear_err", clearErr)
]

# Execution
print("cli.py - GEMS Command Line User Interface")
print("type help for options, type close to stop")

while True:
  userInput = input("> ")
  if userInput == "close":
    break

  words = userInput.split(" ")
  words = [word.strip() for word in words]

  for tuple in inputFunctionTuples:
    if words[0] == tuple[0]:
      tuple[1](words[1:])
      break
  