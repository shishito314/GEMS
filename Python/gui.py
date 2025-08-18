"""
Description:
----------
This file contains the code for the GEMS GUI (Graphical User Interface).

Usage:
----------
When you wish to run the GUI, run this program. The program will stop
when the GUI window is closed.
"""
import tkinter as tk
import tkinter.ttk as ttk

import gems
import gui.config
import gui.graph
import gui.log
import gui.now
import gui.tab
from gui.settings import *
from utilities import *

# -------------------- Window Setup --------------------
window = tk.Tk()
window.title("GEMS Gui")
window.geometry(str(WINDOW_WIDTH) + "x" + str(WINDOW_HEIGHT))
window.resizable(False, False)

# Styling for tab buttons
guiStyle = ttk.Style()
guiStyle.configure(".", foreground=SYSTEM_FONT_COLOR)
guiStyle.configure("Selected.TButton", font=getBoldFont())

guiTabSystem = gui.tab.TabSystem(window)
gloveboxTabSystem = gui.tab.TabSystem(window)
sensorTabSystem = gui.tab.TabSystem(window)

for glovebox in gems.gloveboxes:
    gui.tab.GloveboxTab(glovebox, gloveboxTabSystem, guiTabSystem)

# -------------------- GUI Sections Initialization --------------------
gui.now.Now(window, guiTabSystem, gloveboxTabSystem,
            sensorTabSystem)
gui.graph.Graph(window, guiTabSystem, gloveboxTabSystem,
            sensorTabSystem)
gui.log.Log(window, guiTabSystem, gloveboxTabSystem)
gui.config.Config(window, guiTabSystem)

# -------------------- Window Setup and Launch --------------------
title = ttk.Label(
    master=window, text="Glovebox Environmental Monitoring System")
title.pack()
guiTabSystem.display()
gloveboxTabSystem.currentTab.display()
window.mainloop()
