""" The code imports some modules such as threading, os, importlib, and Path.
It defines two functions, "assessBugClass" and "assessBugType",
which are used to assess bug classes and bug types, respectively.
"""

from bugInvestigator import threadingStyle
import importlib
import os
from pathlib import Path
import re

""" In the "assessBugClass" function, there is a boolean variable "prune" initialized to False.
The function takes a code sample as input and returns the "prune" variable.
It does not appear to modify the input code sample.
It is not clear what this function is used for as it does not perform any operation on the input.
"""


def assessBugClass(codeSample):
    initializationRegex1 = ".+Register.*"
    initializationRegex2 = ".+Circuit.*"

    buggy, patched = codeSample[0], codeSample[1] 
    buggyList = list(filter(("").__ne__, buggy.split("\n")))
    patchedList = list(filter(("").__ne__, patched.split("\n")))

    for line in buggyList:
        status1 = re.search(initializationRegex1, line)
        status2 = re.search(initializationRegex2, line)
        if status1 is not None or status2 is not None:
            return True
    # Does it make search through patched lines too?
    return False


""" In the "assessBugType" function, there are three parameters: bugFolder,
codeSample, and style. The function initializes a boolean variable "prune" to False and an empty string variable "bugTypeMessage".
It gets a list of Python files in the specified "bugFolder" using the "glob" method and imports the modules from each file.
It then executes a "detect" function from each module to detect any bugs in the "codeSample".
If a bug is detected, "prune" is set to True, and the "bugTypeMessage" is updated.
"""


def assessBugType(bugFolder: str, codeSample, astSample, style: threadingStyle):
    prune = False
    bugTypeMessage = ""
    bugDirectoryHandle = Path(__file__).parent.glob("**/*.py")
    bugFiles = [os.path.basename(bugFile) for bugFile in bugDirectoryHandle]
    bugTypeMessages = []
    for bugFile in bugFiles:
        if bugFile == "__init__.py" or bugFile == "probe.py":
            continue
        prober = importlib.import_module(
            bugFolder + "." + bugFile[:-3], f"{bugFolder}.{bugFile}"
        )
        bugDetector = getattr(prober, "detect" + bugFile[:-3])
        status, bugTypeMessage = bugDetector(codeSample, astSample)
        if status == True:
            prune = True
            bugTypeMessages.append(bugTypeMessage)
    return prune, bugTypeMessages
