import platform
import tkinter.font as font

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 625

SYSTEM_FONT_COLOR = "white" if platform.system() == "Darwin" else "black"

# Put into functions because font.nametofont will fail if no window exists
def getSystemFont():
    return font.nametofont("TkDefaultFont").actual()

def getDefaultFont():
    return (getSystemFont(), 14)

def getLargeFont():
    return (getSystemFont(), 18)

def getBoldFont():
    return (getSystemFont(), 14, "bold")