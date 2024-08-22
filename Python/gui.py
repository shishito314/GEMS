# -------------------- File Description --------------------
# This file contains the code for the GEMS GUI (Graphical user interface).
# When you wish to run the GUI, run this program. The program will stop
# when the GUI window is closed.

import tkinter as tk
import tkinter.ttk as ttk
from tkinter import font
from tkinter import scrolledtext
from matplotlib.figure import Figure 
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
import datetime
import os

import gems
import data

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
# -------------------- Utilities + Helpers --------------------
# takes any number of lists and returns a list formed by concatenating the given lists
def listJoin(*args):
	endList = args[0]
	for i in range(1, len(args)):
		endList.extend(args[i])
	return endList

class TabSystem:
	def __init__(self):
		self.container = ttk.Frame(master=window, padding=3)
		self.tabs = []
		self.currentTab = None
	def unDisplay(self):
		self.currentTab.unDisplay()
	def display(self):
		for tab in self.tabs:
			tab.button.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=30)
		self.container.pack()
	def setCurrentTab(self, tab):
		# print(self.currentTab.button._name)
		self.currentTab.button.config(style="Unselected.TButton")
		self.currentTab = tab
		self.currentTab.button.config(style="Selected.TButton")
	def addTab(self, tab):
		self.tabs.append(tab)
		if (len(self.tabs) == 1):
			self.currentTab = tab

class Tab:
	def __init__(self, name, tabSystem, displayFunc):
		self.name = name
		self.tabSystem = tabSystem
		tabSystem.addTab(self)
		self.button = ttk.Button(master=tabSystem.container, text=name, command=self.display, style="Unselected.TButton")
		self.displayFunc = displayFunc
	def unDisplay(self):
		pass
	def display(self):
		self.tabSystem.unDisplay() # the global one
		self.tabSystem.setCurrentTab(self)
		self.displayFunc()

# -------------------- GUI Tab System --------------------
guiTabSystem = TabSystem()
class GuiTab(Tab):
	def __init__(self, name, displayFunc, widgets):
		super().__init__(name, guiTabSystem, displayFunc)
		self.button = ttk.Button(master=guiTabSystem.container, text=name, command=self.display)
		self.displayFunc = displayFunc
		self.widgets = widgets
	def unDisplay(self):
		for widget in self.widgets:
			widget.pack_forget()

# ---------- Now Tab ----------
def showNow():
	# Changing the sensor buttons for the plot if needed
	if prevGlovebox != gloveboxTabSystem.currentTab.glovebox:
		for tab in sensorTabSystem.tabs:
			tab.button.destroy()
			del tab
		sensorTabSystem.tabs = []
		global sensorButtons
		sensorButtons = []
		for sensor in gloveboxTabSystem.currentTab.glovebox.allSensors:
			SensorTab(type(sensor))
	# getting a sensor type if needed
	global nowPlotSensorType
	if not nowPlotSensorType: nowPlotSensorType = sensorTabSystem.currentTab.sensorType
	# Update Readouts
	currentData = data.getAllLastMeasurements(gloveboxTabSystem.currentTab.glovebox)
	readoutLabelsStr = ""
	readoutTimeStampsStr = ""
	readoutValuesStr = ""
	for i in range(0, len(gloveboxTabSystem.currentTab.glovebox.allSensors)):
		sensor = gloveboxTabSystem.currentTab.glovebox.allSensors[i]
		if (i != 0):
			readoutLabelsStr += "\n"
			readoutTimeStampsStr += "\n"
			readoutValuesStr += "\n"
		readoutLabelsStr += sensor.flag
		readoutTimeStampsStr += (gems.getDatetimeStr(currentData[sensor.flag][data.DATA_TIME_FLAG]) if not currentData[sensor.flag][data.DATA_TIME_FLAG] == None else "_____")
		readoutValuesStr += (gems.getDatetimeStr(currentData[sensor.flag][sensor.flag]) if not currentData[sensor.flag][sensor.flag] == None else "_____")
	nowReadoutLabels.config(text=readoutLabelsStr)
	nowReadoutValues.config(text=readoutValuesStr)
	nowReadoutTimeStamps.config(text=readoutTimeStampsStr)

	# Update Plot
	plotData = data.getDataByTime(gloveboxTabSystem.currentTab.glovebox,
																		datetime.datetime.now() - datetime.timedelta(minutes=timeScaleVal),
																		datetime.datetime.now(), nowPlotSensorType)
	fig.clear()
	nowPlot = fig.add_subplot()
	data.subPlotData(nowPlot, plotData, nowPlotSensorType.flag)
	canvas.draw()
	# Pack (display) everything
	gloveboxTabSystem.display()
	readoutLabel.pack(side=tk.LEFT)
	nowReadoutLabels.pack(side=tk.LEFT)
	nowReadoutTimeStamps.pack(side=tk.LEFT)
	nowReadoutValues.pack(side=tk.LEFT)
	nowUpdateButton.pack(side=tk.LEFT)
	readoutContainer.pack()
	nowCanvas.pack()
	toolbar.pack()
	sensorTabSystem.display()
	timeScale.pack(side=tk.LEFT)
	timeScaleButton.pack(side=tk.LEFT)
	timeScaleLabel.pack(side=tk.LEFT)
	timeScaleDisplay.pack(side=tk.LEFT)
	timeControlContainer.pack()
 	# Need to focus on the last packed thing to load things
	sensorTabSystem.container.focus_set()
# For Plot
fig = Figure(figsize = (7, 6), dpi = 100)
canvas = FigureCanvasTkAgg(fig, master=window)
toolbar = NavigationToolbar2Tk(canvas, window=window, pack_toolbar=False) 
toolbar.update()
nowCanvas = canvas.get_tk_widget()
nowCanvas.config(height=350, width=700)
# For Readouts
readoutContainer = ttk.Frame(master=window)
nowReadoutLabels = tk.Message(master=readoutContainer, width=100, font=(defaultFont, 18))
nowReadoutTimeStamps = tk.Message(master=readoutContainer, width=300, font=(defaultFont, 18))
nowReadoutValues = tk.Message(master=readoutContainer, width=100, font=(defaultFont, 18))
readoutLabel = ttk.Label(master=readoutContainer, text="Last Successful Measurements:")
# For Plot Controls
nowPlotSensorType = None
timeControlContainer = ttk.Frame(master=window, width=700, height=30)
timeControlContainer.pack_propagate(False)
MAX_TIME = 1440
def setTimeScale(val):
	val *= (MAX_TIME - 1)
	val += 1
	global timeScaleVal
	timeScaleVal = round(val)
	global timeScaleDisplay
	timeScaleDisplay.config(text=str(round(val)) + " min")
timeScale = ttk.Scale(master=timeControlContainer, command=lambda e:setTimeScale(float(e)), length=500)
timeScaleVal = 60
timeScaleDisplay = tk.Message(master=timeControlContainer, width=100, text=str(timeScaleVal) + " min")
timeScale.set(((timeScaleVal - 1) / (MAX_TIME - 1)))
timeScaleButton = ttk.Button(master=timeControlContainer, text="Go", command=lambda:guiTabSystem.currentTab.display())
timeScaleLabel = ttk.Label(master=timeControlContainer, text="Time:")
# Refresh Button
nowUpdateButton = ttk.Button(master=readoutContainer, text="Update", command=lambda:guiTabSystem.currentTab.display())
# For avoiding unnecessary tasks
prevGlovebox = None
# Widget Lists
plotControlWidgets = [timeControlContainer, timeScale, timeScaleDisplay, timeScaleButton, timeScaleLabel]
readoutWidgets = [readoutContainer, nowReadoutLabels, nowReadoutTimeStamps, nowReadoutValues, readoutLabel]

# ---------- Log Tab ----------
def showLog():
	gloveboxTabSystem.display()
	# logFile = logFileDropdown.selection_get()
	# logText.insert(tk.END, )
	files = os.listdir("./" + gloveboxTabSystem.currentTab.glovebox.name)
	files.sort()
	errorLogFileName = gems.ERROR_LOG_FILE + ".txt"
	hasErrorLog = errorLogFileName in files
	# Rearranging the files so that errorLog is on the top, and then the files are in reverse chronological order
	files.remove(errorLogFileName)
	files.reverse()
	if hasErrorLog:
		files.insert(0, errorLogFileName)

	logFileDropdown.set_menu(files[1], *files) 
	logFileLabel.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
	logFileDropdown.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
	logFileMenuContainer.pack()
	# logText.pack(side=tk.TOP, expand=True, fill=tk.BOTH, padx=20, pady=20)
	showLogFile(files[1])
def showLogFile(e):
	logText.pack_forget()
	global logFileName
	logFileName = e
	logText.config(state="normal")
	logText.delete('1.0', tk.END)
	logFile = open("./" + gloveboxTabSystem.currentTab.glovebox.name + "/" + logFileName, "r")
	logFileStr = logFile.read()
	logFile.close()
	lines = logFileStr.splitlines()
	lineNum = 1
	charNum = len(str(len(lines))) + 1
	displayLog = ""
	for line in lines:
		line = gems.makeStringLength(str(lineNum), charNum) + line + "\n"
		lineNum += 1
		displayLog += line
	logText.insert(tk.END, displayLog)
	logText.config(state="disabled")
	logText.pack(side=tk.TOP, expand=True, fill=tk.BOTH, padx=20, pady=20)

logText = scrolledtext.ScrolledText(master=window)
logFileMenuContainer = ttk.Frame(window)
logFileLabel = ttk.Label(master=logFileMenuContainer, text="File: ")
var = tk.StringVar(window)
logFileDropdown = ttk.OptionMenu(logFileMenuContainer, var, command=lambda e:showLogFile(e))
logFileName = ""

# ---------- Config Tab ----------
def showConfig():
	configText.delete('1.0', tk.END)
	configText.insert(tk.END, open("config.txt").read())
	configText.pack()
	configSave.pack()
def saveConfig():
	log = open("config.txt", "w")
	text = configText.get("1.0", "end-1c")
	log.write(text)
	log.close()

configText = tk.Text(master=window)
configSave = ttk.Button(master=window, text="Save", command=saveConfig)

# -------------------- Glovebox Selecting Buttons --------------------
gloveboxTabSystem = TabSystem()
class GloveboxTab(Tab):
	def __init__(self, glovebox):
		self.glovebox = glovebox
		super().__init__(glovebox.name, gloveboxTabSystem, lambda:guiTabSystem.currentTab.display())
		self.button = ttk.Button(master=gloveboxTabSystem.container, text=glovebox.name, command=self.display)
		gloveboxButtons.append(self.button)
gloveboxButtons = []
for glovebox in gems.gloveboxes:
	GloveboxTab(glovebox)

# -------------------- Sensor Selecting Buttons (For Now Tab) --------------------
sensorTabSystem = TabSystem()
sensorButtons = []
class SensorTab(Tab):
	def __init__(self, sensorType):
		self.sensorType = sensorType
		super().__init__(sensorType.__name__, sensorTabSystem, self.displayingFunc)
		self.button = ttk.Button(master=sensorTabSystem.container, text=sensorType.__name__, command=self.display)
		sensorButtons.append(self.button)
	def displayingFunc(self):
		global nowPlotSensorType
		nowPlotSensorType = self.sensorType
		guiTabSystem.currentTab.display()

# -------------------- GUI Sections Initialization --------------------
# The list of widgets is just things to pack_forget, so we only need the containers for the glovebox and sensor buttons
GuiTab("Now", showNow, [nowCanvas, toolbar, nowUpdateButton, gloveboxTabSystem.container,
	sensorTabSystem.container, readoutContainer, timeControlContainer])
GuiTab("Log", showLog, [logText, logFileMenuContainer, logFileLabel, logFileDropdown, gloveboxTabSystem.container])
GuiTab("Config", showConfig, [configText, configSave])

# -------------------- Window Setup and Launch --------------------
title = ttk.Label(master=window, text="Glovebox Environmental Monitoring System")
title.pack()
guiTabSystem.display()
# guiTabSystem.currentTab.display()
gloveboxTabSystem.currentTab.display()
window.mainloop()
