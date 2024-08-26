# -------------------- File Description --------------------
# This file contains the main loop for the GEMS system. When you wish
# to run the logging and wifi communications, run this program. Once started,
# it will run indefinitely until the program is stopped. You may stop the program
# by closing the python console it is running in.

import time
import gems
import threading

threading.Thread()

# -------------------- Warning Prints --------------------
print("This python console is running GEMS, the Glovebox Environmental Monitoring System.")
print("Please do not close this console unless you wish to stop the program")

# -------------------- Main Run Loop --------------------
initTime = time.time()
waitMarker = initTime

while True:
  if time.time() < waitMarker: continue
  waitMarker += gems.CYCLE_TIMING

  for glovebox in gems.gloveboxes:
    glovebox.update()
