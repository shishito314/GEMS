"""
Description:
----------
This file contains the main loop for the GEMS system. 

Usage:
----------
When you wish to run the logging and wifi communications, run this program.
Once started, it will run indefinitely until the program is stopped.
You may stop the program by closing the python console it is running in.
"""

import datetime
import time
import gems

# -------------------- Warning Prints --------------------
print("\033[91m" + "This python console is running GEMS, the Glovebox Environmental Monitoring System." + "\033[00m")
print("\033[91m" + "Please do not close this console unless you wish to stop the program" + "\033[00m")

# -------------------- Main Run Loop --------------------
initTime = time.time()
waitMarker = initTime

while True:
  for glovebox in gems.gloveboxes:
    try:
      glovebox.update()
    except Exception as e:
      print("There was an error updating " + glovebox.name)
      print(f"{datetime.datetime.now()}\t{e}")

  waitMarker += gems.CYCLE_TIMING
  delay = waitMarker - time.time()
  if delay > 0:
    time.sleep(delay)
