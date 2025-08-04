import tkinter as tk
import tkinter.ttk as ttk
from tkinter import scrolledtext
from typing import Dict, List
import os

from gui.tab import *
from utilities import *

class Log(GuiTab):
    def __init__(self, window, guiTabSystem, gloveboxTabSystem):
        self.gloveboxTabSystem = gloveboxTabSystem

        self.dirs: List[str] = []
        self.files: Dict[str, List[str]] = {}
        self.folderVar = tk.StringVar(window)
        self.fileVar = tk.StringVar(window)

        self.logText = scrolledtext.ScrolledText(master=window)
        self.menuContainer = ttk.Frame(window)
        self.fileLabel = ttk.Label(
            master=self.menuContainer, text="File: ")
        self.folderDropdown = ttk.OptionMenu(
            self.menuContainer, self.folderVar, command=self.changeFolder)
        self.fileDropdown = ttk.OptionMenu(
            self.menuContainer, self.fileVar, command=self.showLogFile)
        super().__init__("log", listJoin([self.logText, self.menuContainer, self.fileLabel,
                                          self.folderDropdown, self.fileDropdown], gloveboxButtons), guiTabSystem)

    def unDisplay(self):
        for widget in self.widgets:
            widget.pack_forget()

    def changeFolder(self, *_):
        folderName = self.folderVar.get()
        self.fileDropdown.set_menu(self.files[folderName][0], *self.files[folderName])
        self.showLogFile()

    def showLogFile(self, *_):
        folderName = self.folderVar.get()
        fileName = self.fileVar.get()
        logFilePath = os.path.join(folderName, fileName)

        if not os.path.exists(logFilePath):
            return

        # Clear and prepare the log display
        self.logText.pack_forget()
        self.logText.config(state="normal")
        self.logText.delete('1.0', tk.END)

        with open(logFilePath, "r") as logFile:
            lines = logFile.readlines()

        # Format with line numbers
        charNum = len(str(len(lines))) + 1
        lineNum = 1
        charNum = len(str(len(lines))) + 1
        displayLog = ""
        for line in lines:
            line = str(lineNum).ljust(charNum) + line
            lineNum += 1
            displayLog += line

        self.logText.insert(tk.END, displayLog)
        self.logText.config(state="disabled")
        self.logText.pack(side=tk.TOP, expand=True, fill=tk.BOTH, padx=20, pady=20)

    def displayFunc(self):
        self.gloveboxTabSystem.display()

        self.dirs.clear()
        self.files.clear()

        walkResult = os.walk(f"./{self.gloveboxTabSystem.currentTab.glovebox.name}")

        for dirPath, _, fileNames in walkResult:
            fileNames = [f for f in fileNames if not f.startswith('.')]
            if fileNames:
                self.dirs.append(dirPath)
                self.files[dirPath] = sorted(fileNames, reverse=True)

        self.dirs.sort()

        if not self.dirs:
            return

        firstDir = self.dirs[0]
        firstFile = self.files[firstDir][0]

        self.folderDropdown.set_menu(firstDir, *self.dirs)
        self.fileDropdown.set_menu(firstFile, *self.files[firstDir])

        self.fileLabel.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        self.folderDropdown.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        self.fileDropdown.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        self.menuContainer.pack()

        self.showLogFile()
