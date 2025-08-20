import ast
import re
import numpy as np
from safeEval import safeEval

class ExcessiveMeasurements():
    def _extractIters(self, node: ast.For):
        target = ast.Name(node.target)
        target_id = target.id
        if isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name) and node.iter.func.id == 'range':
            # Cannot handle range declarations with dynamically calculated endpoints
            if len(node.iter.args) == 1:
                if isinstance(node.iter.args[0], ast.Constant):
                    iterations = node.iter.args[0].value
                    return iterations
            else:
                if isinstance(node.iter.args[0], ast.Constant) and isinstance(node.iter.args[1], ast.Constant):
                    iterations = node.iter.args[1].value - node.iter.args[0].value
                    return iterations
            return None
        elif isinstance(node.iter, ast.List):
            iterations = len(node.iter.elts)
            return iterations


    def _returnArgs(self, args):
        args = "".join(args.split(" "))
        square = []
        paren = []
        value = ""
        parenCheck = 0
        squareCheck = 0

        for char in args:
            if char == "(":
                parenCheck = 1
            elif char == "[":
                squareCheck = 1
            elif char == "]":
                squareCheck = 0
                square.append(value)
                paren.append(square)
                square = []
                value = ""
            elif char == ")":
                parenCheck = 0
                if len(value) > 0:
                    paren.append(value)
            elif char == ",":
                if parenCheck and value != "":
                    if squareCheck:
                        square.append(value)
                    else:
                        paren.append(value)
            else:
                value = ""
                value += char

        for args in range(len(paren)):
            if isinstance(paren[args], list):
                for index in range(len(paren[args])):
                    paren[args][index] = safeEval(paren[args][index], {})
            else:
                paren[args] = safeEval(paren[args], {})

        return np.array(paren)


    def _measurementRegisterError(self, codeSample, astSample):
        # TODO: Deprecate, replace with more robust AST traversal
        availableMeasurementFunctions = ["measure", "measure_all", "measure_inactive"]
        regexPattern = ".+\.measure.*"
        buggy, patched = codeSample[0], codeSample[1]
        buggyMeasures, patchedMeasures = {}, {}
        buggyList = list(filter(("").__ne__, buggy.split("\n")))
        patchedList = list(filter(("").__ne__, patched.split("\n")))
        buggyLine, patchedLine = {}, {}
        buggyArgs, patchedArgs = [], []
        # astBuggy, astPatched = ast.walk(ast.parse(buggy)), ast.walk(ast.parse(patched))
        astBuggy, astPatched = ast.walk(astSample[0]), ast.walk(astSample[1])

        """ Deduce if there is a Quantum Circuit object associated with the patch."""
        for node in astBuggy:
            if isinstance(node, ast.Assign):
                for id in getattr(node, "targets"):
                    if (
                        id.id not in buggyMeasures
                        and isinstance(node.value, ast.Call)
                        and isinstance(node.value.func, ast.Name)
                        and getattr(node, "value").func.id == "QuantumCircuit"
                    ):
                        buggyMeasures[id.id] = []

            """ Using the AST to deduce if there is measure function amongst the aforementioned types."""
            if isinstance(node, ast.Expr):
                if isinstance(node.value.func, ast.Attribute) and getattr(node, "value").func.attr in availableMeasurementFunctions:
                    if getattr(node, "value").func.value.id not in buggyMeasures:
                        buggyMeasures[getattr(node, "value").func.value.id] = []
                        buggyMeasures[getattr(node, "value").func.value.id].append(
                            getattr(node, "value").func.attr
                        )
                    else:
                        buggyMeasures[getattr(node, "value").func.value.id].append(
                            getattr(node, "value").func.attr
                        )

        """ Same checks as above but in the patched code instead of the buggy code."""
        for node in astPatched:
            if isinstance(node, ast.Assign):
                for id in getattr(node, "targets"):
                    if (
                        id.id not in patchedMeasures
                        and isinstance(node.value, ast.Call)
                        and isinstance(node.value.func, ast.Name)
                        and getattr(node, "value").func.id == "QuantumCircuit"
                    ):
                        patchedMeasures[id.id] = []

            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                if isinstance(node.value.func, ast.Attribute) and getattr(node, "value").func.attr in availableMeasurementFunctions:
                    if getattr(node, "value").func.value.id not in patchedMeasures:
                        patchedMeasures[getattr(node, "value").func.value.id] = []
                        patchedMeasures[getattr(node, "value").func.value.id].append(
                            getattr(node, "value").func.attr
                        )
                    else:
                        patchedMeasures[getattr(node, "value").func.value.id].append(
                            getattr(node, "value").func.attr
                        )

        """ Considering the cases when there is a one to one mapping of the QuantumCircuits
        in buggy code to the QuantumCircuits in patched code. """

        if len(buggyMeasures) != len(patchedMeasures):
            return True

        """ Assuming the existence of a singleton Quantum Circuit object,
            deduces if the number of instances of a measurement function
            is equal in both codes."""
        if len(buggyMeasures) != len(patchedMeasures):
            return True

        """ Deduce whether the exact same measure functions are being used in both codes."""
        buggyKeys, patchedKeys = list(buggyMeasures.keys()), list(patchedMeasures.keys())

        for i in range(len(buggyKeys)):
            if buggyMeasures[buggyKeys[i]] != patchedMeasures[patchedKeys[i]]:
                return True

        for line in range(len(buggyList)):
            tempStatus = re.search(regexPattern, buggyList[line])
            # Ensure the commented part is not considered
            code_part = buggyList[line].split('#', 1)[0].strip()
            if tempStatus is not None:
                # buggyLine[buggyList[line].split("measure")[1]] = line
                if "measure_inactive" in buggyList[line]:
                    parts = code_part[line].split("measure_inactive", 1)
                    if len(parts) > 1:
                        buggyLine[parts[1]] = line
                elif "measure_all" in buggyList[line]:
                    parts = code_part[line].split("measure_all", 1)
                    if len(parts) > 1:
                        buggyLine[parts[1]] = line
                elif "measure" in buggyList[line]:
                    parts = code_part[line].split("measure", 1)
                    if len(parts) > 1:
                        buggyLine[parts[1]] = line

        for line in range(len(patchedList)):
            tempStatus = re.search(regexPattern, patchedList[line])
            if tempStatus is not None:
                # patchedLine[patchedList[line].split("measure")[1]] = line
                if "measure_inactive" in patchedList[line]:
                    parts = patchedList[line].split("measure_inactive", 1)
                    if len(parts) > 1:
                        patchedLine[parts[1]] = line
                elif "measure_all" in patchedList[line]:
                    parts = patchedList[line].split("measure_all", 1)
                    if len(parts) > 1:
                        patchedLine[parts[1]] = line
                elif "measure" in patchedList[line]:
                    parts = patchedList[line].split("measure", 1)
                    if len(parts) > 1:
                        patchedLine[parts[1]] = line

        for buggyKey in buggyLine.keys():
            buggyArgs.append(self._returnArgs(buggyKey))

        for patchedKey in patchedLine.keys():
            patchedArgs.append(self._returnArgs(patchedKey))

        if len(buggyArgs) != len(patchedArgs):
            return True

        for i in range(len(buggyArgs)):
            if buggyArgs[i].shape != patchedArgs[i].shape:
                return True
            else:
                if np.array_equal(buggyArgs[i], patchedArgs[i]) == 0:
                    return True

        buggyLineNum = list(buggyLine.values())
        patchedLineNum = list(patchedLine.values())

        """ Optional: can be used to print the exact line numbers of the patch."""
        # print(buggy, patched, sep = "\n***\n")
        # print(buggyLineNum, patchedLineNum)

        for num in range(len(buggyLineNum)):
            if buggyLineNum[num] != patchedLineNum[num]:
                return True

        return False

    def _repeatedMeasurementError(self, codeSample, astSample):
        availableMeasurementFunctions = ["measure", "measure_all", "measure_inactive"]
        regexPattern = ".+\.measure.*"

        buggy, patched = codeSample[0], codeSample[1]
        buggyMeasures, patchedMeasures = {}, {}
        astBuggy, astPatched = ast.walk(astSample[0]), ast.walk(astSample[1])

        for node in astBuggy:
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                for target in node.targets:
                    if (target.id not in buggyMeasures
                            and isinstance(node.value.func, ast.Name)
                            and node.value.func.id == 'QuantumCircuit'):
                        buggyMeasures[target.id] = 0

        for node in astPatched:
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                for target in node.targets:
                    if (target.id not in patchedMeasures
                            and isinstance(node.value.func, ast.Name)
                            and node.value.func.id == 'QuantumCircuit'):
                        patchedMeasures[target.id] = 0




        astBuggy, astPatched = ast.walk(ast.parse(buggy)), ast.walk(ast.parse(patched))
        buggyCircIDs, patchedCircIDs = buggyMeasures.keys(), patchedMeasures.keys()

        for node in astBuggy:
            if isinstance(node, ast.For):
                iterations = self._extractIters(node)
                if not iterations:
                    continue
                else:
                    for subnode in node.body:
                        if isinstance(subnode, ast.Expr) and isinstance(subnode.value, ast.Call):
                            id = subnode.value.func.value.id
                            func = subnode.value.func.attr
                            if id in buggyMeasures.keys() and func in availableMeasurementFunctions:
                                buggyMeasures[id] += iterations - 1
            else:
                if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute):
                    if isinstance(node.value.func.value, ast.Name):
                        id = node.value.func.value.id
                    func = node.value.func.attr
                    if id in buggyMeasures.keys() and func in availableMeasurementFunctions:
                        buggyMeasures[id] += 1


        for node in astPatched:
            if isinstance(node, ast.For):
                iterations = self._extractIters(node)
                if not iterations:
                    continue
                else:
                    for subnode in node.body:
                        if isinstance(subnode, ast.Expr) and isinstance(subnode.value, ast.Call):
                            id = subnode.value.func.value.id
                            func = subnode.value.func.attr
                            if id in patchedMeasures.keys() and func in availableMeasurementFunctions:
                                patchedMeasures[id] += iterations - 1
            else:
                if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute):
                    if isinstance(node.value.func.value, ast.Name):
                        id = node.value.func.value.id
                        func = node.value.func.attr
                    if id in patchedMeasures.keys() and func in availableMeasurementFunctions:
                        patchedMeasures[id] += 1

        for id in buggyCircIDs:
            if id in patchedCircIDs:
                if buggyMeasures[id] > patchedMeasures[id]:
                    return True

        return False


    def _detectIncorrectMeasurement(self, codeSample, astSample):
        status = False
        bugTypeMessage2 = "Excessive measurements performed"
        try:
            status = self._repeatedMeasurementError(codeSample, astSample)
            print("repeatedMeasurement WORKS")
        except:
            status = False
            # status2 = True
            print("error in repeatedMeasurementError")
            raise
        bugTypeMessage = ''
        if status:
            bugTypeMessage += bugTypeMessage2 + '.'

        return status, bugTypeMessage
    
    def assessBugType(self, codeSample, astSample):
        return self._detectIncorrectMeasurement(codeSample, astSample)