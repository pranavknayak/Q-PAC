import ast
import re
import numpy as np

class Initialization():
    def __init__(self, dummy=""):
        self.testing = dummy


    def assessBugType(self, codeSample, astSample):
        initializationRegex1 = ".+Register.*"
        initializationRegex2 = ".+Circuit.*"

        buggy, patched = codeSample[0], codeSample[1] 
        buggyList = list(filter(("").__ne__, buggy.split("\n")))
        patchedList = list(filter(("").__ne__, patched.split("\n")))

        for line in buggyList:
            status1 = re.search(initializationRegex1, line)
            status2 = re.search(initializationRegex2, line)
            if status1 is not None or status2 is not None:
                return True, 'None'
        # Does it make search through patched lines too?
        return False, 'None'