# -------------------- File Description --------------------
# This file contains contains various utility methods used across the other files.

import datetime # for getting the time

# -------------------- Utility Functions --------------------
# ---------- Text Parsing Utilities ----------
# Gets the text between a given start and end flag
def readFromUntil(text, flagStart, flagEnd):
  prev = text[0:len(flagStart)]
  startIndex = len(flagStart)
  while (prev != flagStart) and (startIndex < len(text)):
    startIndex += 1
    prev = text[(startIndex - len(flagStart)):(startIndex)]
  prev = text[startIndex:(startIndex+len(flagEnd))]
  endIndex = startIndex
  while (prev != flagEnd) and (endIndex < len(text)):
    endIndex += 1
    prev = text[(endIndex):(endIndex + len(flagEnd))]
  return text[startIndex:endIndex]
# readFromUntil, but returns None if flagEnd isn't found
def readFromUntilRequireEnd(text, flagStart, flagEnd):
  prev = text[0:len(flagStart)]
  startIndex = len(flagStart)
  while (prev != flagStart) and (startIndex < len(text)):
    startIndex += 1
    prev = text[(startIndex - len(flagStart)):(startIndex)]
  prev = text[startIndex:(startIndex+len(flagEnd))]
  endIndex = startIndex
  while (prev != flagEnd) and (endIndex < len(text)):
    endIndex += 1
    prev = text[(endIndex):(endIndex + len(flagEnd))]
  if prev != flagEnd:
    return None
  return text[startIndex:endIndex]
# Gets the text up until a given flag
def readUntil(text, flag):
  prev = text[0:len(flag)]
  index = len(flag)
  while (prev != flag) and (index < len(text)):
    index += 1
    prev = text[(index - len(flag)):(index)]
  return text[0:index - len(flag)]
# Gets the text from a given start flag until any of the given end flags
def readFromUntilFlags(text, flagStart, flagsEnd):
  prev = text[0:len(flagStart)]
  startIndex = len(flagStart)
  while (prev != flagStart) and (startIndex < len(text)):
    startIndex += 1
    prev = text[(startIndex - len(flagStart)):(startIndex)]
  # prev = text[startIndex:(startIndex+len(flagEnd))]
  endIndex = startIndex
  done = False
  while not done:
    endIndex += 1
    for flag in flagsEnd:
      if text[endIndex:endIndex+len(flag)] == flag:
        done = True
    if endIndex >= len(text):
      done = True
  # while (prev != flagEnd) and (endIndex < len(text)):
  #   endIndex += 1
  #   prev = text[(endIndex):(endIndex + len(flagEnd))]
  return text[startIndex:endIndex]
# Gets all the text after a given flag
def readFrom(text, flag):
  prev = text[0:len(flag)]
  index = len(flag)
  while (prev != flag) and (index < len(text)):
    index += 1
    prev = text[(index - len(flag)):(index)]
  return text[index:len(text)]
# Gets the index where the flag starts (i.e. the first character of the flag)
def getFlagStartIndex(text, flag):
  prev = text[0:len(flag)]
  index = 0
  while (prev != flag) and (index < (len(text) - len(flag))):
    index += 1
    prev = text[index:(index + len(flag))]
  return index
# Gets the index where the flag ends (i.e. one character after the flag)
def getFlagEndIndex(text, flag):
  prev = text[0:len(flag)]
  index = len(flag)
  while (prev != flag) and (index < len(text)):
    index += 1
    prev = text[(index - len(flag)):(index)]
  return index
# removes all the spaces in a string
def removeSpaces(text):
  return text.replace(" ", "")
# adds whitespace if the text is shorter than the specified length. If not, doesn't do anything.
def makeStringLength(text, length):
  if len(text) < length:
    for i in range(length - len(text)):
      text += " "
  return text

# ---------- Datetime Utilities ----------
# returns a datetime object for the passed string, using the "yr-month-day hr:min:sec.decimal" format
def convertStrToDatetime(string):
  return datetime.datetime.strptime(string, "%Y-%m-%d %H:%M:%S.%f")
# returns a datetime object for the passed string, using the "yr-month-day" format
def convertStrToDate(string):
  return datetime.datetime.strptime(string, "%Y-%m-%d").date()
# returns a timeDelta that is the difference between two times given as strings
def timeDiffFromString(start, stop):
    tStart = datetime.datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
    tStop = datetime.datetime.strptime(stop, "%Y-%m-%d %H:%M:%S")
    return tStop - tStart

# ---------- Miscellaneous Utilities ----------
def sortDictionariesByValue(listOfDictionaries, key):
  listOfDictionaries.sort(key=lambda d: d[key])
# maps a value in a certain range to another range
def map(l1, h1, l2, h2, val):
  return (val-l1) / (h1-l1) * (h2-l2) + l2
