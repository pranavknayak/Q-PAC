import importlib
import os
from pathlib import Path
import sys

sys.path.insert(0, "../Q-AutoDiaBFM/src")
import bugInvestigator as bI

bugDatasetRootDirectoryName = "bugDataset"
bugDatasetRootDirectoryPath = "../Q-AutoDiaBFM/tests/bugDataset"

""" Runs all tests for all bug detection modules."""


def runTests(
    bugTestFiles,
    bugDatasetDirectoryName,
    bugDatasetDirectoryPath,
    characteristicBugMessage,
):
    allTestsPassed = False
    bugCounter = 1
    failedTestFiles = []
    numberOfTestsPassed = 0

    for bugTestFile in bugTestFiles:
        bugTestFileName = os.path.basename(bugTestFile)
        bugTestFileProber = importlib.import_module(
            bugDatasetDirectoryName + "." + bugTestFileName[:-3],
           f"{bugDatasetDirectoryPath}.{bugTestFileName}",
        )
        bugTypeMessage = bI.classifyBugs(
            bugTestFileProber.buggyCode,
            bugTestFileProber.patchedCode,
            commandLine=False,
        )
        success = 0
        for type in bugTypeMessage:
            if characteristicBugMessage in bugTypeMessage[type]:
                numberOfTestsPassed += 1
                success = 1
        if not success:
            failedTestFiles.append((bugCounter, bugTypeMessage, bugTestFile))
        # numberOfTestsPassed += bugTypeMessage == characteristicBugMessage
        bugCounter += 1

    allTestsPassed = numberOfTestsPassed == len(bugTestFiles)//2

    if not allTestsPassed:
        print(
            f"{len(bugTestFiles) - numberOfTestsPassed} / {len(bugTestFiles)} tests failed! Failed tests are displayed below:\n"
        )
        for bugIndex, bugTypeMessage, failedTestFile in failedTestFiles:
            print(
                "<===============================",
                f"Test {bugIndex}",
                "===============================>",
                "\n",
            )
            with open(failedTestFile) as bugFormatter:
                print(bugFormatter.read())
            print("(Wrong) error message:", bugTypeMessage, "\n")
    return allTestsPassed


def testIncorrectGate():
    allTestsPassed = False
    bugTypeName = "IncorrectGate"
    bugDatasetDirectoryName = bugDatasetRootDirectoryName + "." + bugTypeName
    bugDatasetDirectoryPath = bugDatasetRootDirectoryPath + "/" + bugTypeName
    bugTestFilesHandler = Path(bugDatasetDirectoryPath).glob(
        "**/" + bugTypeName + "*.py"
    )
    bugTestFiles = [bugTestFile for bugTestFile in bugTestFilesHandler]
    characteristicBugMessage = "Incorrect usage of gate(s)."

    print("Testing incorrect usage of gate(s).")
    allTestsPassed = runTests(
        bugTestFiles,
        bugDatasetDirectoryName,
        bugDatasetDirectoryPath,
        characteristicBugMessage,
    )
    if allTestsPassed:
        print("All tests for detecting incorrect usage of gate(s) have passed!")
    return allTestsPassed


def testIncorrectInit():
    allTestsPassed = False
    bugTypeName = "IncorrectInit"
    bugDatasetDirectoryName = bugDatasetRootDirectoryName + "." + bugTypeName
    bugDatasetDirectoryPath = bugDatasetRootDirectoryPath + "/" + bugTypeName
    bugTestFilesHandler = Path(bugDatasetDirectoryPath).glob(
        "**/" + bugTypeName + "*.py"
    )
    bugTestFiles = [bugTestFile for bugTestFile in bugTestFilesHandler]
    characteristicBugMessage = "Incorrect initialization(s) attempted."

    print("Testing for the presence of incorrect initialization(s).")
    allTestsPassed = runTests(
        bugTestFiles,
        bugDatasetDirectoryName,
        bugDatasetDirectoryPath,
        characteristicBugMessage,
    )
    if allTestsPassed:
        print(
            "All tests for detecting the presesnce of incorrect initialization(s) have passed!"
        )
    return allTestsPassed


def testIncorrectMeasurement():
    allTestsPassed = False
    bugTypeName = "IncorrectMeasurement"
    bugDatasetDirectoryName = bugDatasetRootDirectoryName + "." + bugTypeName
    bugDatasetDirectoryPath = bugDatasetRootDirectoryPath + "/" + bugTypeName
    bugTestFilesHandler = Path(bugDatasetDirectoryPath).glob(
        "**/" + bugTypeName + "*.py"
    )
    bugTestFiles = [bugTestFile for bugTestFile in bugTestFilesHandler]
    characteristicBugMessage = "Measurement(s) performed incorrectly."

    print("Testing for the presence of incorrectly performed measurement(s).")
    allTestsPassed = runTests(
        bugTestFiles,
        bugDatasetDirectoryName,
        bugDatasetDirectoryPath,
        characteristicBugMessage,
    )
    if allTestsPassed:
        print(
            "All tests for detecting the presence of incorrectly performed measurement(s) have passed!"
        )
    return allTestsPassed


"""
def testIncorrectQubitCount():
    allTestsPassed = False
    bugTypeName = "IncorrectQubitCount"
    bugDatasetDirectoryName = bugDatasetRootDirectoryName + "." + bugTypeName
    bugDatasetDirectoryPath = bugDatasetRootDirectoryPath + "/" + bugTypeName
    bugTestFilesHandler = Path(bugDatasetDirectoryPath).glob(
        "**/" + bugTypeName + "*.py"
    )
    bugTestFiles = [bugTestFile for bugTestFile in bugTestFilesHandler]
    characteristicBugMessage = "Incorrect number of qubits used."

    print("Testing usage of incorrect number of qubits.")
    allTestsPassed = runTests(
        bugTestFiles,
        bugDatasetDirectoryName,
        bugDatasetDirectoryPath,
        characteristicBugMessage,
    )
    if allTestsPassed:
        print(
            "All tests for detecting usage of incorrect number of qubits have passed!"
        )
    return allTestsPassed


def testIncorrectQubitOrder():
    allTestsPassed = False
    bugTypeName = "IncorrectQubitOrder"
    bugDatasetDirectoryName = bugDatasetRootDirectoryName + "." + bugTypeName
    bugDatasetDirectoryPath = bugDatasetRootDirectoryPath + "/" + bugTypeName
    bugTestFilesHandler = Path(bugDatasetDirectoryPath).glob(
        "**/" + bugTypeName + "*.py"
    )
    bugTestFiles = [bugTestFile for bugTestFile in bugTestFilesHandler]
    characteristicBugMessage = "Incorrect order of qubits used."

    print("Testing usage of incorrect order of qubits.")
    allTestsPassed = runTests(
        bugTestFiles,
        bugDatasetDirectoryName,
        bugDatasetDirectoryPath,
        characteristicBugMessage,
    )
    if allTestsPassed:
        print("All tests for detecting usage of incorrect order of qubits have passed!")
    return allTestsPassed
"""


def runAllTests():
    status = testIncorrectGate() | testIncorrectInit() | testIncorrectMeasurement()
    if status == True:
        print("All tests have passed!")
    return status
