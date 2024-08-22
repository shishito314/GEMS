# -------------------- File Description --------------------
# Simple script to print the latest sensor measurements

import gems
import data

print("Last successful logs:")

for glovebox in gems.gloveboxes:
  print(glovebox.name)
  currentData = data.getAllLastMeasurements(glovebox)
  for sensor in glovebox.allSensors:
    print(sensor.flag, end="\t")
    print(gems.getDatetimeStr(currentData[sensor.flag][data.DATA_TIME_FLAG]) if not currentData[sensor.flag][data.DATA_TIME_FLAG] == None else "_____", end="\t")
    print(gems.getDatetimeStr(currentData[sensor.flag][sensor.flag]) if not currentData[sensor.flag][sensor.flag] == None else "_____")
