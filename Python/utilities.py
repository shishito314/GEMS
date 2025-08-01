"""
Description:
----------
Various utility methods for use in other files.
"""
import datetime
from typing import List, Optional
import os

# -------------------- Text Parsing Utilities --------------------
def readFromUntil(text: str, flagStart: str, flagEnd: str) -> str:
    """Extracts text between flagStart and flagEnd (exclusive)."""
    startIdx = text.find(flagStart)
    if startIdx == -1:
        return ''
    startIdx += len(flagStart)
    endIdx = text.find(flagEnd, startIdx)
    return text[startIdx:endIdx] if endIdx != -1 else text[startIdx:]

def readFromUntilRequireEnd(text: str, flagStart: str, flagEnd: str) -> Optional[str]:
    """Like readFromUntil, but returns None if flagEnd isn't found."""
    startIdx = text.find(flagStart)
    if startIdx == -1:
        return None
    startIdx += len(flagStart)
    endIdx = text.find(flagEnd, startIdx)
    return text[startIdx:endIdx] if endIdx != -1 else None

def readUntil(text: str, flag: str) -> str:
    """Returns text up to the first occurrence of flag."""
    idx = text.find(flag)
    return text[:idx] if idx != -1 else text

def readFromUntilFlags(text: str, flagStart: str, flagsEnd: List[str]) -> str:
    """Gets the text starting after flagStart and ending at the first of any flagsEnd."""
    startIdx = text.find(flagStart)
    if startIdx == -1:
        return ''
    startIdx += len(flagStart)

    endIdx = len(text)
    for flag in flagsEnd:
        idx = text.find(flag, startIdx)
        if 0 <= idx < endIdx:
            endIdx = idx

    return text[startIdx:endIdx]

def readFrom(text: str, flag: str) -> str:
    """Returns text after the first occurrence of flag."""
    idx = text.find(flag)
    return text[idx + len(flag):] if idx != -1 else ''

def removeSpaces(text: str) -> str:
    """Removes all spaces from the string."""
    return text.replace(' ', '')

# -------------------- Datetime Utilities --------------------
def strToDatetime(string: str) -> datetime.datetime:
    """Converts string of format 'YYYY-MM-DD HH:MM:SS.ssssss' or 'YYYY-MM-DD HH:MM:SS' to datetime."""
    try:
        return datetime.datetime.strptime(string, "%Y-%m-%d %H:%M:%S.%f")
    except:
        return datetime.datetime.strptime(string, "%Y-%m-%d %H:%M:%S")

def strToDate(string: str) -> datetime.date:
    """Converts string of format 'YYYY-MM-DD' to date."""
    return datetime.datetime.strptime(string, "%Y-%m-%d").date()

def strToTime(string: str) -> datetime.time:
    """Converts string of format 'HH:MM:SS.ssssss' or 'HH:MM:SS' to time."""
    try:
        return datetime.datetime.strptime(string, "%H:%M:%S.%f").time()
    except:
        return datetime.datetime.strptime(string, "%H:%M:%S").time()

# -------------------- Miscellaneous Utilities --------------------
def mapValue(l1: float, h1: float, l2: float, h2: float, val: float) -> float:
    """Maps a value from range [l1, h1] to range [l2, h2]."""
    return (val - l1) / (h1 - l1) * (h2 - l2) + l2

def listJoin(*args: List) -> List:
    """Takes any number of lists and returns a list formed by concatenating them."""
    endList = args[0]
    for i in range(1, len(args)):
        endList.extend(args[i])
    return endList

def makeDirIfNotExist(path):
    """Creates the given directory if it doesn't exist."""
    if not os.path.isdir(path):
        os.mkdir(path)

def getTimeDurationStr(minutes: int) -> str:
    days = minutes // (60 * 24)
    minutes %= (60 * 24)
    hours = minutes // 60
    minutes %= 60

    parts = []
    if days:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    parts.append(f"{minutes} min")

    return ", ".join(parts)
