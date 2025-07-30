
import tkinter as tk
import tkinter.ttk as ttk
from gui.tab import *
from utilities import *
import data
import gems

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)

MAX_TIME = 14400

class Now(GuiTab):
    def __init__(self, window, guiTabSystem, gloveboxTabSystem, sensorTabSystem, defaultFont):
        self.gloveboxTabSystem = gloveboxTabSystem
        self.sensorTabSystem = sensorTabSystem

        # Plotting Elements
        self.fig = Figure(figsize=(7, 6), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=window)
        self.toolbar = NavigationToolbar2Tk(self.canvas, window=window, pack_toolbar=False)
        self.toolbar.update()
        self.nowCanvas = self.canvas.get_tk_widget()
        self.nowCanvas.config(height=350, width=700)
        # Readout Elements
        self.readoutContainer = ttk.Frame(master=window)
        self.nowReadoutLabels = tk.Message(master=self.readoutContainer, width=100, font=(defaultFont, 18))
        self.nowReadoutTimeStamps = tk.Message(master=self.readoutContainer, width=300, font=(defaultFont, 18))
        self.nowReadoutValues = tk.Message(master=self.readoutContainer, width=100, font=(defaultFont, 18))
        self.readoutLabel = ttk.Label(master=self.readoutContainer, text="Last Successful Measurements:")
        # Plot Controls Elements
        self.nowPlotSensorType = None
        self.timeControlContainer = ttk.Frame(master=window, width=700, height=30)
        self.timeControlContainer.pack_propagate(False)
        self.timeScale = ttk.Scale(master=self.timeControlContainer, command=lambda e: self.setTimeScale(float(e)), length=400)
        self.timeScaleVal = 60
        self.timeScaleDisplay = tk.Message(master=self.timeControlContainer, width=200, text=str(self.timeScaleVal) + " min")
        self.timeScale.set(((self.timeScaleVal - 1) / (MAX_TIME - 1)))
        self.timeScaleButton = ttk.Button(master=self.timeControlContainer, text="Go", command=lambda: guiTabSystem.currentTab.display())
        self.timeScaleLabel = ttk.Label(master=self.timeControlContainer, text="Time:")
        # Refresh Button
        self.nowUpdateButton = ttk.Button(master=self.readoutContainer, text="Update", command=lambda: guiTabSystem.currentTab.display())

        self.prevGlovebox = None
        self.sensorButtons = None

        # Widget Lists
        self.plotControlWidgets = [
            self.timeControlContainer, self.timeScale,
            self.timeScaleDisplay, self.timeScaleButton, self.timeScaleLabel
        ]
        self.readoutWidgets = [
            self.readoutContainer, self.nowReadoutLabels,
            self.nowReadoutTimeStamps, self.nowReadoutValues, self.readoutLabel
        ]

        super().__init__(
            "now",
            listJoin(
                self.plotControlWidgets, self.readoutWidgets,
                [self.toolbar, self.nowCanvas, self.sensorTabSystem.container, self.nowUpdateButton], gloveboxButtons,
            ),
            guiTabSystem
        )

    def setTimeScale(self, val):
        val *= (MAX_TIME - 1)
        val += 1
        val = round(val)
        self.timeScaleVal = val
        days = val // (60 * 24)
        val -= days * 60 * 24
        hours = val // 60
        val -= hours * 60
        timeScaleStr = ""
        if not days:
            if not hours:
                timeScaleStr = f"{val} min"
            else:
                timeScaleStr = f"{hours} hour{"s" if hours != 1 else ""}, {val} min"
        else:
            timeScaleStr = f"{days} day{"s" if days != 1 else ""}, {hours} hour{"s" if hours != 1 else ""}, {val} min"
        self.timeScaleDisplay.config(text=timeScaleStr)

    def unDisplay(self):
        for tab in self.sensorTabSystem.tabs:
            tab.button.destroy()
        return super().unDisplay()

    def displayFunc(self):
        # Changing the sensor buttons for the plot if needed
        if self.prevGlovebox != self.gloveboxTabSystem.currentTab.glovebox:
            for tab in self.sensorTabSystem.tabs:
                tab.button.destroy()
                del tab
            self.sensorTabSystem.tabs = []

            self.widgets = listJoin(self.plotControlWidgets, self.readoutWidgets, [self.toolbar, self.nowCanvas], gloveboxButtons)

            self.sensorButtons = []
            for sensor in self.gloveboxTabSystem.currentTab.glovebox.allSensors:
                sensorTab = SensorTab(type(sensor), self.sensorTabSystem, self.tabSystem, self)
                self.widgets.append(sensorTab.button)
        # getting a sensor type if needed
        # print(self.sensorTabSystem.currentTab.sensorType)
        if not self.nowPlotSensorType:
            self.nowPlotSensorType = self.sensorTabSystem.currentTab.sensorType
        # Update Readouts
        currentData = data.getLastMeasurementAllSensors(self.gloveboxTabSystem.currentTab.glovebox)
        readoutLabelsStr = ""
        readoutTimeStampsStr = ""
        readoutValuesStr = ""
        for i in range(0, len(self.gloveboxTabSystem.currentTab.glovebox.allSensors)):
            sensor = self.gloveboxTabSystem.currentTab.glovebox.allSensors[i]
            if (i != 0):
                readoutLabelsStr += "\n"
                readoutTimeStampsStr += "\n"
                readoutValuesStr += "\n"
            readoutLabelsStr += sensor.__class__.__name__
            readoutTimeStampsStr += (gems.getDatetimeStr(currentData[sensor.flag][data.DATA_TIME_FLAG]) if not currentData[sensor.flag][data.DATA_TIME_FLAG] == None else "_____")
            readoutValuesStr += (gems.getDatetimeStr(currentData[sensor.flag][data.DATA_MEASUREMENTS_FLAG]) if not currentData[sensor.flag][data.DATA_MEASUREMENTS_FLAG] == None else "_____")
        self.nowReadoutLabels.config(text=readoutLabelsStr)
        self.nowReadoutValues.config(text=readoutValuesStr)
        self.nowReadoutTimeStamps.config(text=readoutTimeStampsStr)

        # Update Plot
        plotData = data.getDataByTime(self.gloveboxTabSystem.currentTab.glovebox, datetime.datetime.now() - datetime.timedelta(minutes=self.timeScaleVal), datetime.datetime.now(), self.nowPlotSensorType)
        self.fig.clear()
        nowPlot = self.fig.add_subplot()
        data.subPlotData(nowPlot, plotData, title=self.nowPlotSensorType.flag)
        self.canvas.draw()
        # Pack (display) everything
        self.gloveboxTabSystem.display()
        self.readoutLabel.pack(side=tk.LEFT)
        self.nowReadoutLabels.pack(side=tk.LEFT)
        self.nowReadoutTimeStamps.pack(side=tk.LEFT)
        self.nowReadoutValues.pack(side=tk.LEFT)
        self.nowUpdateButton.pack(side=tk.LEFT)
        self.readoutContainer.pack()
        self.nowCanvas.pack()
        self.toolbar.pack()
        self.sensorTabSystem.display()
        self.timeScale.pack(side=tk.LEFT)
        self.timeScaleButton.pack(side=tk.LEFT)
        self.timeScaleLabel.pack(side=tk.LEFT)
        self.timeScaleDisplay.pack(side=tk.LEFT)
        self.timeControlContainer.pack()
        # Need to focus on the last packed thing to load things
        self.sensorTabSystem.container.focus_set()
