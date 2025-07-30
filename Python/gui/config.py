import tkinter as tk
import tkinter.ttk as ttk
from gui.tab import *

class Config(GuiTab):
    def __init__(self, window, guiTabSystem):
        self.configText = tk.Text(master=window)
        self.configSave = ttk.Button(master=window, text="Save", command=self.saveConfig)
        super().__init__("config", [self.configText, self.configSave], guiTabSystem)
    
    def saveConfig(self):
        log = open("config.txt", "w")
        text = self.configText.get("1.0", "end-1c")
        log.write(text)
        log.close()
    
    def displayFunc(self):
        self.configText.delete('1.0', tk.END)
        self.configText.insert(tk.END, open("config.txt").read())
        self.configText.pack()
        self.configSave.pack()
