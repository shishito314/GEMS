
import tkinter as tk
import tkinter.ttk as ttk
from typing import List

class TabSystem:
    def __init__(self, window):
        self.container = ttk.Frame(master=window, padding=3)
        self.tabs: List[Tab] = []
        self.currentTab: Tab = None

    def unDisplay(self):
        """Cleans up when switching tabs."""
        self.currentTab.unDisplay()

    def display(self):
        """Show"""
        for tab in self.tabs:
            tab.button.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=30)
        self.container.pack()

    def setCurrentTab(self, tab):
        self.currentTab.button.config(style="TButton")
        self.currentTab = tab
        self.currentTab.button.config(style="Selected.TButton")

    def addTab(self, tab):
        self.tabs.append(tab)
        if (len(self.tabs) == 1):
            self.currentTab = tab

class Tab:
    def __init__(self, name, tabSystem):
        self.name: str = name
        self.tabSystem: TabSystem = tabSystem
        tabSystem.addTab(self)
        self.button = ttk.Button(master=tabSystem.container, text=name, command=self.display, style="TButton")

    def unDisplay(self):
        pass

    def display(self):
        self.tabSystem.unDisplay()  # the global one
        self.tabSystem.setCurrentTab(self)
        self.displayFunc()

    def displayFunc(self):
        raise NotImplementedError("Tab displayFunc not implemented")

# -------------------- GUI Tab System --------------------
class GuiTab(Tab):
    def __init__(self, name, widgets, guiTabSystem):
        super().__init__(name, guiTabSystem)
        self.button = ttk.Button(master=guiTabSystem.container, text=name, command=self.display)
        self.widgets: List[tk.Widget] = widgets

    def unDisplay(self):
        for widget in self.widgets:
            widget.pack_forget()

# -------------------- Glovebox Selecting Buttons --------------------
gloveboxButtons = []
class GloveboxTab(Tab):
    def __init__(self, glovebox, gloveboxTabSystem, guiTabSystem):
        self.glovebox = glovebox
        self.guiTabSystem = guiTabSystem
        self.button = ttk.Button(master=gloveboxTabSystem.container, text=glovebox.name, command=self.display)
        gloveboxButtons.append(self.button)
        super().__init__(glovebox.name, gloveboxTabSystem)

    def displayFunc(self):
        self.guiTabSystem.currentTab.display()

# -------------------- Sensor Selecting Buttons (For Now Tab) --------------------
class SensorTab(Tab):
    def __init__(self, sensorType, sensorTabSystem, guiTabSystem, nowTab):
        self.sensorType = sensorType
        self.guiTabSystem = guiTabSystem
        self.nowTab = nowTab
        self.button = ttk.Button(master=sensorTabSystem.container, text=sensorType.__name__, command=self.display)
        super().__init__(sensorType.__name__, sensorTabSystem)

    def displayFunc(self):
        self.guiTabSystem.currentTab.display()
