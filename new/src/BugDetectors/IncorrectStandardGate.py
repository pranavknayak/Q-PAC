import ast
import re
import numpy as np

class IncorrectStandardGate():
    def _inbuiltGateError(self, codeSample, astSample):
        availableInbuiltGates = [
            "ccx",
            "cx",
            "cz",
            "h",
            "i",
            "p",
            "s",
            "sdg",
            "t",
            "tdg",
            "u",
            "x",
            "y",
            "z",
            "swap"
        ]
        regexPattern = r".+\..*"

        buggy, patched = codeSample[0], codeSample[1]
        buggyID, patchedID = {}, {}
        buggyList = list(filter(("").__ne__, buggy.split("\n")))
        patchedList = list(filter(("").__ne__, patched.split("\n")))
        buggyGate, patchedGate = [], []
        # astBuggy, astPatched = ast.walk(ast.parse(buggy)), ast.walk(ast.parse(patched))
        astBuggy, astPatched = ast.walk(astSample[0]), ast.walk(astSample[1])
        buggyRegs, patchedRegs = {}, {}
        buggy_int_vals, patched_int_vals = {}, {}

        """ Retrieves all instances of a QuantumCircuit object in both, the buggy and patched codes."""
        for node in astBuggy:
            if isinstance(node, ast.Assign):
                for id in getattr(node, "targets"):
                    if isinstance(id, ast.Name):
                        if isinstance(node.value, ast.Constant):
                            buggy_int_vals[id.id] = node.value.value
                        elif (
                            id.id not in buggyID
                            and isinstance(node.value, ast.Call)
                            and isinstance(node.value.func, ast.Name)
                            and getattr(node, "value").func.id == "QuantumCircuit"
                        ):
                            qubits = 0
                            args = node.value.args
                            if len(args) > 0 and isinstance(args[0], ast.Constant):
                                qubits = args[0].value
                            elif len(args) > 0 and isinstance(args[0], ast.Name):
                                if args[0].id in buggyRegs:
                                    qubits = buggyRegs[args[0].id]
                                elif args[0].id in buggy_int_vals:
                                    qubits = buggy_int_vals[args[0].id]
                            buggyID[id.id] = [0] * qubits
                        elif (
                            id.id not in buggyRegs
                            and isinstance(node.value, ast.Call)
                            and isinstance(node.value.func, ast.Name)
                            and node.value.func.id == "QuantumRegister"
                        ):
                            if isinstance(node.value.args[0], ast.Name):
                                buggyRegs[id.id] = buggy_int_vals[node.value.args[0].id]
                            else:
                                buggyRegs[id.id] = node.value.args[0].value



        for node in astPatched:
            if isinstance(node, ast.Assign):
                for id in getattr(node, "targets"):
                    if isinstance(id, ast.Name):
                        qubits = 0
                        if isinstance(node.value, ast.Constant):
                            patched_int_vals[id.id] = node.value.value
                        elif (
                            id.id not in patchedID
                            and isinstance(node.value, ast.Call)
                            and isinstance(node.value.func, ast.Name)
                            and getattr(node, "value").func.id == "QuantumCircuit" # Throwing bug, investigate further.
                        ):
                            args = node.value.args
                            if isinstance(args[0], ast.Constant):
                                qubits = args[0].value
                            elif isinstance(args[0], ast.Name):
                                if args[0].id in patchedRegs:
                                    qubits = patchedRegs[args[0].id]
                                elif args[0].id in patched_int_vals:
                                    qubits = patched_int_vals[args[0].id]

                            patchedID[id.id] = [0] * qubits
                        elif (
                            id.id not in patchedRegs
                            and isinstance(node.value, ast.Call)
                            and isinstance(node.value.func, ast.Name)
                            and node.value.func.id == "QuantumRegister"
                        ):
                            if isinstance(node.value.args[0], ast.Name):
                                patchedRegs[id.id] = patched_int_vals[node.value.args[0].id]
                            else:
                                patchedRegs[id.id] = node.value.args[0].value

        """ Considering the cases when there is a one to one mapping of the QuantumCircuits
        in buggy code to the QuantumCircuits in patched code. """
        # if len(buggyID) != len(patchedID):
        #     print("HIIHIHIHIH\n")
        #     print(buggyID)
        #     print(patchedID)
        #     return True

        """ Checks if the gate is amongst the available gates in Qiskit."""
        for line in buggyList:
            temporaryStatus = re.search(regexPattern, line)
            if temporaryStatus is not None:
                iden = line.split(".")[0]
                gate = line.split(".")[1].split("(")[0]
                if iden in buggyID and gate in availableInbuiltGates:
                    buggyGate.append(gate)

        for line in patchedList:
            temporaryStatus = re.search(regexPattern, line)
            if temporaryStatus is not None:
                iden = line.split(".")[0]
                gate = line.split(".")[1].split("(")[0]
                if iden in patchedID and gate in availableInbuiltGates:
                    patchedGate.append(gate)

        """ Checks if the number of gates used in both codes are the same."""
        if set(buggyGate) != set(patchedGate):
            return True

        """ Checks if any of the gates used are differenet, line by line in both the codes."""
        for index in range(len(buggyGate)):
            if buggyGate[index] != patchedGate[index]:
                return True

        return False

    def _customGateError(self, codeSample, astSample):
        buggy, patched = codeSample[0], codeSample[1]
        buggyList = list(filter(("").__ne__, buggy.split("\n")))
        patchedList = list(filter(("").__ne__, patched.split("\n")))
        # astBuggy, astPatched = ast.walk(ast.parse(buggy)), ast.walk(ast.parse(patched))
        astBuggy, astPatched = ast.walk(astSample[0]), ast.walk(astSample[1])
        buggyGateIDs = {}
        buggyCustomIDs = {}

        for node in astBuggy:
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if (target.id not in buggyGateIDs
                                and isinstance(node.value.func, ast.Name)
                                and node.value.func.id == 'Gate'):
                            gate = node.value
                            for argument in gate.args:
                                if isinstance(argument, ast.Constant) and argument.value > 2:
                                    buggyGateIDs[target.id] = []
                                    break
                            for kwargument in gate.keywords:
                                if kwargument.arg == 'num_qubits' and kwargument.value.value > 2:
                                    buggyGateIDs[target.id] = []
                                    break

                        if (target.id not in buggyCustomIDs
                                and isinstance(node.value.func, ast.Attribute)
                                and node.value.func.attr == 'to_instruction'):
                            buggyCustomIDs[target.id] = []




        patchedGateIDs = {}
        patchedCustomIDs = {}
        for node in astPatched:
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if (target.id not in patchedGateIDs
                                and isinstance(node.value.func, ast.Name)
                                and node.value.func.id == 'Gate'):
                            gate = node.value
                            for argument in gate.args:
                                if isinstance(argument, ast.Constant) and argument.value > 2:
                                    patchedGateIDs[target.id] = []
                                    break
                            for kwargument in gate.keywords:
                                if kwargument.arg == 'num_qubits' and kwargument.value.value > 2:
                                    patchedGateIDs[target.id] = []
                                    break

                        if (target.id not in patchedCustomIDs
                                and isinstance(node.value.func, ast.Attribute)
                                and node.value.func.attr == 'to_instruction'):
                            patchedCustomIDs[target.id] = []

        buggyGateCount, buggyCustomCount = len(buggyGateIDs), len(buggyCustomIDs)
        patchedGateCount, patchedCustomCount = len(patchedGateIDs), len(patchedCustomIDs)

        if buggyGateCount > patchedGateCount:
            opaqueGateReduction = buggyGateCount - patchedGateCount
            compositeGateIncrease = patchedCustomCount - buggyCustomCount
            if opaqueGateReduction <= compositeGateIncrease:
                return True

        return False


    # def _detectIncorrectGate(self, codeSample, astSample):
    #     status = False
    #     bugTypeMessage1 = "Incorrect usage of built-in gate(s)"
    #     bugTypeMessage2 = "Incorrect usage of opaque gate(s)"
    #     try:
    #         status1 = self._inbuiltGateError(codeSample, astSample)
    #         print("InbuiltGateError WORKS")
    #     except:
    #         status1 = False
    #         print("error in inbuiltGateError")
    #         raise

    #     try:
    #         status2 = self._customGateError(codeSample, astSample)
    #         print("CustomGateError WORKS")
    #     except:
    #         status2 = False
    #         print("error in customGateError")
    #         raise

    #     bugTypeMessage = ''
    #     if status1 and status2:
    #         bugTypeMessage = bugTypeMessage1 + " and " + bugTypeMessage2 + '.'
    #     elif status1:
    #         bugTypeMessage = bugTypeMessage1 + '.'
    #     elif status2:
    #         bugTypeMessage = bugTypeMessage2 + '.'
    #     status = status1 or status2

    #     return status, bugTypeMessage
    def _detectIncorrectGate(self, codeSample, astSample):
        status = False
        bugTypeMessage1 = "Incorrect usage of built-in gate(s)"
        try:
            status = self._inbuiltGateError(codeSample, astSample)
            print("InbuiltGateError WORKS")
        except:
            status = False
            print("error in inbuiltGateError")
            raise

        bugTypeMessage = ''
        if status:
            bugTypeMessage = bugTypeMessage1 + '.'

        return status, bugTypeMessage
    

    def assessBugType(self, codeSample, astSample):
        return self._detectIncorrectGate(codeSample, astSample)
