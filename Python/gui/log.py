import tkinter as tk
import tkinter.ttk as ttk
from gui.tab import *
from tkinter import scrolledtext
from utilities import *
import gems

import os

class Log(GuiTab):
    def __init__(self, window, guiTabSystem, gloveboxTabSystem):
        self.gloveboxTabSystem = gloveboxTabSystem
        self.logText = scrolledtext.ScrolledText(master=window)
        self.logFileMenuContainer = ttk.Frame(window)
        self.logFileLabel = ttk.Label(master=self.logFileMenuContainer, text="File: ")
        self.var = tk.StringVar(window)
        self.logFileDropdown = ttk.OptionMenu(self.logFileMenuContainer, self.var, command=lambda e:self.showLogFile(e))
        self.logFileName = ""
        super().__init__("log", listJoin([self.logText, self.logFileMenuContainer, self.logFileLabel, self.logFileDropdown], gloveboxButtons), guiTabSystem)

    def unDisplay(self):
        for widget in self.widgets:
            widget.pack_forget()
    def showLogFile(self, e):
        self.logText.pack_forget()
        self.logFileName = e
        self.logText.config(state="normal")
        self.logText.delete('1.0', tk.END)
        logFile = open(self.logFileName, "r")
        logFileStr = logFile.read()
        logFile.close()
        lines = logFileStr.splitlines()
        lineNum = 1
        charNum = len(str(len(lines))) + 1
        displayLog = ""
        for line in lines:
            line = str(lineNum).ljust(charNum) + line + "\n"
            lineNum += 1
            displayLog += line
        self.logText.insert(tk.END, displayLog)
        self.logText.config(state="disabled")
        self.logText.pack(side=tk.TOP, expand=True, fill=tk.BOTH, padx=20, pady=20)
    def displayFunc(self):
        self.gloveboxTabSystem.display()
        walkResult = os.walk("./" + self.gloveboxTabSystem.currentTab.glovebox.name)
        files = []
        for dirPath, _, fileNames in walkResult:
            if dirPath == "./" + self.gloveboxTabSystem.currentTab.glovebox.name + "/" + gems.ERROR_LOG_FOLDER:
                continue
            for fileName in fileNames:
                files.append(os.path.join(dirPath, fileName))
        files.sort()
        # errorLogFileName = "./" + self.gloveboxTabSystem.currentTab.glovebox.name + "/" + gems.ERROR_LOG_FILE + ".txt" # TODO
        # hasErrorLog = errorLogFileName in files
        # Rearranging the files so that errorLog is on the top, and then the files are in reverse chronological order
        # files.remove(errorLogFileName)
        # files.reverse()
        # if hasErrorLog:
        #     files.insert(0, errorLogFileName)

        self.logFileDropdown.set_menu(files[1], *files) 
        self.logFileLabel.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        self.logFileDropdown.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        self.logFileMenuContainer.pack()
        self.showLogFile(files[1])