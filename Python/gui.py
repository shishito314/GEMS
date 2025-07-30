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
from tkinter import font

import gems
from utilities import *
import gui.now
import gui.log
import gui.config
import gui.tab

# -------------------- Constants --------------------
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 625

# -------------------- Window Setup --------------------
window = tk.Tk()
window.title("GEMS Gui")
window.geometry(str(WINDOW_WIDTH) + "x" + str(WINDOW_HEIGHT))
window.resizable(False, False)

# Styling for tab buttons
guiStyle = ttk.Style()
defaultFont = font.nametofont("TkDefaultFont").actual()
guiStyle.configure("Selected.TButton", foreground="white", font=(defaultFont, defaultFont["size"], 'bold'))
guiStyle.configure("Unselected.TButton", foreground="white")

guiTabSystem = gui.tab.TabSystem(window)
gloveboxTabSystem = gui.tab.TabSystem(window)
sensorTabSystem = gui.tab.TabSystem(window)

for glovebox in gems.gloveboxes:
	gui.tab.GloveboxTab(glovebox, gloveboxTabSystem, guiTabSystem)

# -------------------- GUI Sections Initialization --------------------
# The list of widgets is just things to pack_forget, so we only need the containers for the glovebox and sensor buttons
gui.now.Now(window, guiTabSystem, gloveboxTabSystem, sensorTabSystem, defaultFont)
gui.log.Log(window, guiTabSystem, gloveboxTabSystem)
gui.config.Config(window, guiTabSystem)

# -------------------- Window Setup and Launch --------------------
title = ttk.Label(master=window, text="Glovebox Environmental Monitoring System")
title.pack()
guiTabSystem.display()
gloveboxTabSystem.currentTab.display()
window.mainloop()