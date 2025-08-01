import tkinter as tk
import tkinter.ttk as ttk

import gems
from gui.tab import *

HELP_TEXT = """Here's the format for a config file:

Glovebox: [Name]
Arduino: IP: [IP Adress] Display: [True/False] Sensors: [Sensor1 Sensor2...]
Arduino: IP: [IP Adress] Display: [True/False] Sensors: [Sensor1 Sensor2...]
Glovebox: [Name]
[Arduinos...]
...

Here's an example of a config file following that format:

Glovebox: pluto
Arduino: IP: 192.168.0.110 Display: True Sensors: Oxy Water
Arduino: IP: 192.168.0.111 Display: False Sensors: Temp
Glovebox: neptune
Arduino: IP: 192.168.0.112 Display: True Sensors: Oxy
Arduino: IP: 192.168.0.113 Display: False Sensors: Temp

IMPORTANT: Capitalization and the colons after words are mandatory.
"""

class Config(GuiTab):
    def __init__(self, window, guiTabSystem):
        self.configText = tk.Text(master=window)
        self.configSave = ttk.Button(
            master=window, text="Save", command=self.saveConfig)
        self.helpButton = ttk.Button(
            master=window, text="Help", command=self.showHelp)
        super().__init__(
            "config", [self.configText, self.configSave, self.helpButton], guiTabSystem)

    def saveConfig(self):
        text = self.configText.get("1.0", "end-1c")
        with open(gems.CONFIG_FILE, "w") as log:
            log.write(text)

    def showHelp(self):
        helpWindow = tk.Toplevel()
        helpWindow.title("Config Help")
        helpWindow.geometry("600x400")

        helpTextWidget = tk.Text(helpWindow, wrap="word")
        helpTextWidget.insert("1.0", HELP_TEXT)
        helpTextWidget.configure(state="disabled")  # make read-only
        helpTextWidget.pack(expand=True, fill="both", padx=10, pady=10)

        # Optional: add a close button for user convenience
        closeButton = ttk.Button(
            helpWindow, text="Close", command=helpWindow.destroy)
        closeButton.pack(pady=(0, 10))

    def displayFunc(self):
        self.configText.delete('1.0', tk.END)
        with open(gems.CONFIG_FILE) as file:
            fileText = file.read()
        self.configText.insert(tk.END, fileText)
        self.configText.pack()
        self.configSave.pack()
        self.helpButton.pack()
