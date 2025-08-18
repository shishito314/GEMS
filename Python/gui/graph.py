import calendar
import datetime
import tkinter as tk
import tkinter.ttk as ttk

import data
from gui.tab import *
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
                                               NavigationToolbar2Tk)
from matplotlib.figure import Figure
from utilities import *

MAX_TIME = 1440

class Graph(GuiTab):
    def __init__(self, window, guiTabSystem, gloveboxTabSystem, sensorTabSystem):
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

        # --- Plot Controls Elements ---
        self.timeControlContainer = ttk.Frame(
            master=window, width=700, height=30)
        self.timeControlContainer.pack_propagate(False)

        self.startLabel = ttk.Label(self.timeControlContainer, text="Start:")
        self.endLabel = ttk.Label(self.timeControlContainer, text="End:")

        # Register field-specific validation commands
        self.vcmd_year = window.register(self._validate_year)
        self.vcmd_month = window.register(lambda val: self._validate_num_range(val, 1, 12))
        self.vcmd_day_start = window.register(lambda val: self._validate_day(val, self.startYear, self.startMonth))
        self.vcmd_day_end = window.register(lambda val: self._validate_day(val, self.endYear, self.endMonth))
        self.vcmd_hour = window.register(lambda val: self._validate_num_range(val, 0, 23))
        self.vcmd_minute = window.register(lambda val: self._validate_num_range(val, 0, 59))

        # Start time inputs
        self.startYear = ttk.Entry(self.timeControlContainer, width=5, validate="key", validatecommand=(self.vcmd_year, "%P"))
        self.startMonth = ttk.Entry(self.timeControlContainer, width=3, validate="key", validatecommand=(self.vcmd_month, "%P"))
        self.startDay = ttk.Entry(self.timeControlContainer, width=3, validate="key", validatecommand=(self.vcmd_day_start, "%P"))
        self.startHour = ttk.Entry(self.timeControlContainer, width=3, validate="key", validatecommand=(self.vcmd_hour, "%P"))
        self.startMinute = ttk.Entry(self.timeControlContainer, width=3, validate="key", validatecommand=(self.vcmd_minute, "%P"))

        # End time inputs
        self.endYear = ttk.Entry(self.timeControlContainer, width=5, validate="key", validatecommand=(self.vcmd_year, "%P"))
        self.endMonth = ttk.Entry(self.timeControlContainer, width=3, validate="key", validatecommand=(self.vcmd_month, "%P"))
        self.endDay = ttk.Entry(self.timeControlContainer, width=3, validate="key", validatecommand=(self.vcmd_day_end, "%P"))
        self.endHour = ttk.Entry(self.timeControlContainer, width=3, validate="key", validatecommand=(self.vcmd_hour, "%P"))
        self.endMinute = ttk.Entry(self.timeControlContainer, width=3, validate="key", validatecommand=(self.vcmd_minute, "%P"))

        self.timeWarningLabel = ttk.Label(window, text="", foreground="red")

        for entry in [self.startYear, self.startMonth, self.startDay, self.startHour, self.startMinute,
              self.endYear, self.endMonth, self.endDay, self.endHour, self.endMinute]:
            entry.bind("<KeyRelease>", lambda event: self._check_time_order())

        # Default values
        now = datetime.datetime.now()
        ten_minutes_ago = now - datetime.timedelta(minutes=10)
        self._setDateTimeEntries(self.startYear, self.startMonth, self.startDay,
                                 self.startHour, self.startMinute, ten_minutes_ago)
        self._setDateTimeEntries(self.endYear, self.endMonth, self.endDay,
                                 self.endHour, self.endMinute, now)

        self.timeScaleButton = ttk.Button(
            master=self.timeControlContainer, text="Go", command=lambda: guiTabSystem.currentTab.display())

        # --- Widget Lists ---
        self.plotControlWidgets = [
            self.timeControlContainer,
            self.startLabel, self.startYear, self.startMonth, self.startDay, self.startHour, self.startMinute,
            self.endLabel, self.endYear, self.endMonth, self.endDay, self.endHour, self.endMinute,
            self.timeScaleButton,
            self.timeWarningLabel
        ]

        super().__init__(
            "graph",
            listJoin(
                self.plotControlWidgets,
                [self.toolbar, self.nowCanvas,
                    self.sensorTabSystem.container],
                gloveboxButtons,
            ),
            guiTabSystem
        )

    def displayFunc(self):
        self.gloveboxTabSystem.display()
        # Changing the sensor buttons for the plot if needed
        if self.prevGlovebox != self.gloveboxTabSystem.currentTab.glovebox:
            self.prevGlovebox = self.gloveboxTabSystem.currentTab.glovebox
            self._rebuildSensorTabs()

        self.nowPlotSensorType = self.sensorTabSystem.currentTab.sensorType

        self._drawPlot()

        self._packWidgets()

    def _drawPlot(self):
        startTime, endTime = self._getValidatedTimes()
        if not startTime or not endTime:
            return  # Don't plot if invalid input

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
            [self.toolbar, self.nowCanvas],
            gloveboxButtons
        )

        self.sensorButtons = []
        for sensor in self.gloveboxTabSystem.currentTab.glovebox.allSensors:
            sensorTab = SensorTab(
                type(sensor), self.sensorTabSystem, self.tabSystem, self)
            self.widgets.append(sensorTab.button)
        self.sensorTabSystem.setCurrentTab(self.sensorTabSystem.tabs[0])

    def _packWidgets(self):
        """Handles packing of all dynamic widgets."""

        # Plot
        self.nowCanvas.pack()
        self.toolbar.pack()

        # Sensor Buttons
        self.sensorTabSystem.display()

        # Time Controls
        self.startLabel.pack(side=tk.LEFT)
        self.startYear.pack(side=tk.LEFT)
        self.startMonth.pack(side=tk.LEFT)
        self.startDay.pack(side=tk.LEFT)
        self.startHour.pack(side=tk.LEFT)
        self.startMinute.pack(side=tk.LEFT)

        self.endLabel.pack(side=tk.LEFT)
        self.endYear.pack(side=tk.LEFT)
        self.endMonth.pack(side=tk.LEFT)
        self.endDay.pack(side=tk.LEFT)
        self.endHour.pack(side=tk.LEFT)
        self.endMinute.pack(side=tk.LEFT)

        self.timeScaleButton.pack(side=tk.RIGHT)

        self.timeControlContainer.pack()
        self.timeWarningLabel.pack()

        self.sensorTabSystem.container.focus_set()

    def _setDateTimeEntries(self, yearEntry, monthEntry, dayEntry, hourEntry, minuteEntry, dt):
        yearEntry.insert(0, dt.year)
        monthEntry.insert(0, dt.month)
        dayEntry.insert(0, dt.day)
        hourEntry.insert(0, dt.hour)
        minuteEntry.insert(0, dt.minute)

    def _getValidatedTimes(self):
        # try:
        start = datetime.datetime(
            int(self.startYear.get()), int(self.startMonth.get()), int(self.startDay.get()),
            int(self.startHour.get()), int(self.startMinute.get()))
        end = datetime.datetime(
            int(self.endYear.get()), int(self.endMonth.get()), int(self.endDay.get()),
            int(self.endHour.get()), int(self.endMinute.get()))

        if start >= end:
            raise ValueError("Start time must be before end time.")

        return start, end

        # except ValueError as ve:
        #     messagebox.showerror("Invalid Input", f"Time input error: {ve}")
        #     return None, None
        # except Exception as e:
        #     messagebox.showerror("Invalid Input", f"Unexpected error: {e}")
        #     return None, None

    def _validate_year(self, val):
        year = datetime.datetime.now().year
        if val == "" or (val.isdigit() and int(val) <= year):
            return True
        return False
    
    def _validate_day(self, val, yearEntry, monthEntry):
        if val == "":
            return True
        if not val.isdigit():
            return False

        day = int(val)
        try:
            year = int(yearEntry.get())
            month = int(monthEntry.get())
            if 1 <= month <= 12:
                _, max_day = calendar.monthrange(year, month)
                return 1 <= day <= max_day
            else:
                return 1 <= day <= 31
        except ValueError:
            return 1 <= day <= 31

    def _validate_num_range(self, val, min, max):
        if val == "" or (val.isdigit() and min <= int(val) <= max):
            return True
        return False
    
    def _check_time_order(self):
        try:
            start = datetime.datetime(
                int(self.startYear.get()), int(self.startMonth.get()), int(self.startDay.get()),
                int(self.startHour.get()), int(self.startMinute.get()))
            end = datetime.datetime(
                int(self.endYear.get()), int(self.endMonth.get()), int(self.endDay.get()),
                int(self.endHour.get()), int(self.endMinute.get()))

            if start >= end:
                self.timeWarningLabel.config(text="⚠️ End time must be after start time")
            else:
                self.timeWarningLabel.config(text="")
        except:
            self.timeWarningLabel.config(text="")  # Ignore partial inputs
