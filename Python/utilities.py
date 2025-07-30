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

# -------------------- Miscellaneous Utilities --------------------

def mapValue(l1: float, h1: float, l2: float, h2: float, val: float) -> float:
    """Maps a value from one range to another."""
    return (val - l1) / (h1 - l1) * (h2 - l2) + l2

# takes any number of lists and returns a list formed by concatenating the given lists
def listJoin(*args):
	endList = args[0]
	for i in range(1, len(args)):
		endList.extend(args[i])
	return endList

def makeDirIfNotExist(path):
    if not os.path.isdir(path):
      os.mkdir(path)
