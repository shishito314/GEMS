import tkinter as tk
import tkinter.ttk as ttk

import data
import gems
from gui.tab import *
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
                                               NavigationToolbar2Tk)
from matplotlib.figure import Figure
from utilities import *

MAX_TIME = 14400

class Now(GuiTab):
    def __init__(self, window, guiTabSystem, gloveboxTabSystem, sensorTabSystem, defaultFont):
        self.gloveboxTabSystem = gloveboxTabSystem
        self.sensorTabSystem = sensorTabSystem

        self.prevGlovebox = None
        self.sensorButtons = None
        self.nowPlotSensorType = None
        self.timeScaleVal = 30

        # --- Plotting Elements ---
        self.fig = Figure(figsize=(7, 6), dpi=100, tight_layout=True)
        self.canvas = FigureCanvasTkAgg(self.fig, master=window)
        self.toolbar = NavigationToolbar2Tk(
            self.canvas, window=window, pack_toolbar=False)
        self.toolbar.update()
        self.nowCanvas = self.canvas.get_tk_widget()
        self.nowCanvas.config(height=350, width=700)

        # --- Readout Elements ---
        self.readoutContainer = ttk.Frame(master=window)
        self.nowReadoutLabels = tk.Message(
            master=self.readoutContainer, width=100, font=(defaultFont, 18))
        self.nowReadoutTimeStamps = tk.Message(
            master=self.readoutContainer, width=300, font=(defaultFont, 18))
        self.nowReadoutValues = tk.Message(
            master=self.readoutContainer, width=100, font=(defaultFont, 18))
        self.readoutLabel = ttk.Label(
            master=self.readoutContainer, text="Last Successful Measurements:")

        # --- Plot Controls Elements ---
        self.timeControlContainer = ttk.Frame(
            master=window, width=700, height=30)
        self.timeControlContainer.pack_propagate(False)
        self.timeScale = ttk.Scale(
            master=self.timeControlContainer, command=self.setTimeScale, length=400)
        self.timeScaleDisplay = tk.Message(
            master=self.timeControlContainer, width=200, text=str(self.timeScaleVal) + " min")
        self.timeScale.set(((self.timeScaleVal - 1) / (MAX_TIME - 1)))
        self.timeScaleButton = ttk.Button(
            master=self.timeControlContainer, text="Go", command=lambda: guiTabSystem.currentTab.display())
        self.timeScaleLabel = ttk.Label(
            master=self.timeControlContainer, text="Time:")

        # --- Refresh Button ---
        self.nowUpdateButton = ttk.Button(
            master=self.readoutContainer, text="Update", command=lambda: guiTabSystem.currentTab.display())

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
                self.plotControlWidgets,
                self.readoutWidgets,
                [self.toolbar, self.nowCanvas,
                    self.sensorTabSystem.container, self.nowUpdateButton],
                gloveboxButtons,
            ),
            guiTabSystem
        )

    def setTimeScale(self, val):
        val = round(float(val) * (MAX_TIME - 1) + 1)
        self.timeScaleVal = val
        self.timeScaleDisplay.config(text=getTimeDurationStr(val))

    def unDisplay(self):
        for tab in self.sensorTabSystem.tabs:
            tab.button.destroy()
        return super().unDisplay()

    def displayFunc(self):
        # Changing the sensor buttons for the plot if needed
        if self.prevGlovebox != self.gloveboxTabSystem.currentTab.glovebox:
            self._rebuildSensorTabs()
            # getting a sensor type if needed
        if not self.nowPlotSensorType:
            self.nowPlotSensorType = self.sensorTabSystem.currentTab.sensorType

        self._updateReadouts()

        self._drawPlot()

        self._packWidgets()

    def _drawPlot(self):
        startTime = datetime.datetime.now() - datetime.timedelta(minutes=self.timeScaleVal)
        endTime = datetime.datetime.now()

        plotData = data.getDataByTime(self.gloveboxTabSystem.currentTab.glovebox,
                                      self.nowPlotSensorType, startTime, endTime)
        plotErrors = data.getErrorsByTime(
            self.gloveboxTabSystem.currentTab.glovebox, self.nowPlotSensorType, startTime, endTime)

        self.fig.clear()
        nowPlot = self.fig.add_subplot()
        nowPlot.tick_params(axis='x', labelrotation=45)
        data.subPlotData(nowPlot, plotData,
                         title=self.nowPlotSensorType.__name__)
        data.subPlotErrors(nowPlot, plotErrors, color="red")
        self.canvas.draw()

    def _rebuildSensorTabs(self,):
        """Regenerates sensor tab buttons when glovebox changes."""
        for tab in self.sensorTabSystem.tabs:
            tab.button.destroy()
            del tab
        self.sensorTabSystem.tabs = []

        self.widgets = listJoin(
            self.plotControlWidgets,
            self.readoutWidgets,
            [self.toolbar, self.nowCanvas, self.nowUpdateButton],
            gloveboxButtons
        )

        self.sensorButtons = []
        for sensor in self.gloveboxTabSystem.currentTab.glovebox.allSensors:
            sensorTab = SensorTab(
                type(sensor), self.sensorTabSystem, self.tabSystem, self)
            self.widgets.append(sensorTab.button)

    def _packWidgets(self):
        """Handles packing of all dynamic widgets."""
        # Readout
        self.readoutLabel.pack(side=tk.LEFT)
        self.nowReadoutLabels.pack(side=tk.LEFT)
        self.nowReadoutTimeStamps.pack(side=tk.LEFT)
        self.nowReadoutValues.pack(side=tk.LEFT)
        self.nowUpdateButton.pack(side=tk.LEFT)
        self.readoutContainer.pack()

        # Plot
        self.nowCanvas.pack()
        self.toolbar.pack()

        # Sensor Buttons
        self.sensorTabSystem.display()

        # Time Controls
        self.timeScale.pack(side=tk.LEFT)
        self.timeScaleButton.pack(side=tk.LEFT)
        self.timeScaleLabel.pack(side=tk.LEFT)
        self.timeScaleDisplay.pack(side=tk.LEFT)
        self.timeControlContainer.pack()

        self.sensorTabSystem.container.focus_set()

    def _updateReadouts(self):
        currentData = data.getLastMeasurementAllSensors(
            self.gloveboxTabSystem.currentTab.glovebox)
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
            readoutTimeStampsStr += (gems.getDateTimeStr(currentData[sensor.flag][data.DATA_TIME_KEY])
                                     if currentData[sensor.flag][data.DATA_TIME_KEY] else "_____")
            readoutValuesStr += (str(currentData[sensor.flag][data.DATA_MEASUREMENT_KEY])
                                 if not currentData[sensor.flag][data.DATA_MEASUREMENT_KEY] == None else "_____")
        self.nowReadoutLabels.config(text=readoutLabelsStr)
        self.nowReadoutValues.config(text=readoutValuesStr)
        self.nowReadoutTimeStamps.config(text=readoutTimeStampsStr)
