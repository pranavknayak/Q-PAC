import ast
import re
import numpy as np

class Measurement():
    def __init__(self, dummy=""):
        self.testing = dummy
    
    def assessBugType(self, codeSample, astSample):
        measurementRegex = ".+measure.*"
        buggy, patched = codeSample[0], codeSample[1]
        buggyList = list(filter(("").__ne__, buggy.split("\n")))
        # patchedList = list(filter(("").__ne__, patched.split("\n")))

        for line in buggyList:
            status = re.search(measurementRegex, line)
            if status is not None:
                return True, 'None'

        return False, 'None'