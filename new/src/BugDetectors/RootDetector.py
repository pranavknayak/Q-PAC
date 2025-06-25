class RootDetector():
    def __init__(self, dummy=""):
        self.testing = dummy
    
    def assessBugType(self, codeSample, astSample):
        return True, 'None'