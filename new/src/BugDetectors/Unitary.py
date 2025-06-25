import ast
import re
import numpy as np

class Unitary():
    def __init__(self, dummy=""):
        self.testing = dummy
    
    def assessBugType(self, codeSample, astSample):
        unitaryRegex1 = ".+Gate.*"
        unitaryRegex2 = r"\.h\(.*\)"
        unitaryRegex3 = r".+\..*"
        buggy, patched = codeSample[0], codeSample[1]
        buggyList = list(filter(("").__ne__, buggy.split("\n")))
        for line in buggyList:
            status = re.search(unitaryRegex1, line)
            if status is not None:
                return True, 'None'

        for line in buggyList:
            status = re.search(unitaryRegex2, line)
            if status is not None:
                return True, 'None'
        for line in buggyList:
            status = re.search(unitaryRegex3, line)
            if status is not None:
                return True, 'None'
        return False, 'None'