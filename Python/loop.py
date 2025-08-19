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
import os
import time
import traceback

import gems

# -------------------- Warning Prints --------------------
try:
    TERMINAL_WIDTH = os.get_terminal_size().columns
except:
    TERMINAL_WIDTH = 50
print(f"\n{'-' * TERMINAL_WIDTH}")
print("This python console is running GEMS, the Glovebox Environmental Monitoring System.")
print("Please DO NOT CLOSE THIS TERMINAL unless you wish to stop the program.")
print(f"{'-' * TERMINAL_WIDTH}\n")

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
