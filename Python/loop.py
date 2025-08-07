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
import traceback

import gems

# -------------------- Warning Prints --------------------
print("This python console is running GEMS, the Glovebox Environmental Monitoring System.")
print("Please do not close this console unless you wish to stop the program.")

# -------------------- Main Run Loop --------------------
initTime = time.time()
waitMarker = initTime

while True:
    for glovebox in gems.gloveboxes:
        try:
            glovebox.update()
        except Exception as e:
            print(f"{datetime.datetime.now()} There was an error updating {glovebox.name}")
            traceback.print_exc()

    waitMarker += gems.CYCLE_TIMING
    delay = waitMarker - time.time()
    if delay > 0:
        time.sleep(delay)
