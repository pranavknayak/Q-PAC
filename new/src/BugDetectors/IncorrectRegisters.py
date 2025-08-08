import ast
import re
import numpy as np

class IncorrectRegisters():
    def _checkIncorrectRegisters(self, codeSample, astSample):

        classicalRegex = ".+ClassicalRegister.*"
        quantumRegex = ".+QuantumRegister.*"
        integerRegex = ".+=\s[0-9]+"
        functionCallRegex = ".+\(.*\)"

        buggy, patched = codeSample[0], codeSample[1]
        buggyList = list(filter(("").__ne__, buggy.split("\n")))
        patchedList = list(filter(("").__ne__, patched.split("\n")))

        buggyClassicalRegisters = {}
        buggyQuantumRegisters = {}
        patchedClassicalRegisters = {}
        patchedQuantumRegisters = {}

        # astBuggy, astPatched = ast.walk(ast.parse(buggy)), ast.walk(ast.parse(patched))
        astBuggy, astPatched = ast.walk(astSample[0]), ast.walk(astSample[1])

        # Literal tracking:

        buggyInts, patchedInts = {}, {}
        for line in buggyList:
            intStatus = re.search(integerRegex, line)
            funcStatus = re.search(functionCallRegex, line)
            if intStatus is None:
                continue
            if funcStatus is not None:
                continue
            args = [arg.strip() for arg in line.split('=')]
            if ',' not in args[0]: #handle multiple assignment later
                if args[0].isnumeric():
                    buggyInts[args[0]] = float(args[1])

        for line in patchedList:
            intStatus = re.search(integerRegex, line)
            funcStatus = re.search(functionCallRegex, line)
            if intStatus is None:
                continue
            if funcStatus is not None:
                continue
            args = [arg.strip() for arg in line.split('=')]
            if ',' not in args[0]: #handle multiple assignment later
                if args[0].isnumeric():
                    patchedInts[args[0]] = float(args[1])



        for line in buggyList:
            temporaryStatus = re.search(classicalRegex, line)
            if temporaryStatus is not None and "import" not in line:
                register = line.split('=')[0].strip()
                args = (line.split('ClassicalRegister')[1])
                if ',' in args:
                    count_str = args[1: args.index(',')]
                    if count_str in buggyInts:
                        count = buggyInts[count_str]
                    elif count_str.isnumeric():
                        count = int(count_str)
                    else:
                        count = 0
                else:
                    # print(args, args[1:2])
                    count = int(args[1:2])
                buggyClassicalRegisters[register] = count

            temporaryStatus = re.search(quantumRegex, line)
            if temporaryStatus is not None and "import" not in line:
                register = line.split('=')[0].strip()
                args = (line.split('QuantumRegister')[1]).strip()
                if ',' in args:
                    count_str = args[1: args.index(',')]
                    if count_str in buggyInts:
                        count = buggyInts[count_str]
                    elif count_str.isnumeric():
                        count = int(count_str)
                    else:
                        count = 0
                else:
                    # count = int(args[1:-1])
                    count = int(args[1:2])
                buggyQuantumRegisters[register] = count

        for line in patchedList:
            temporaryStatus = re.search(classicalRegex, line)
            if temporaryStatus is not None and "import" not in line:
                register = line.split('=')[0].strip()
                args = (line.split('ClassicalRegister')[1]).strip()
                if ',' in args:
                    count_str = args[1: args.index(',')]
                    if count_str in patchedInts:
                        count = patchedInts[count_str]
                    elif count_str.isnumeric():
                        count = int(count_str)
                    else:
                        count = 0
                else:
                    count = int(args[1:-1])
                patchedClassicalRegisters[register] = count

            temporaryStatus = re.search(quantumRegex, line)
            if temporaryStatus is not None and "import" not in line:
                register = line.split('=')[0].strip()
                args = (line.split('QuantumRegister')[1])
                if ',' in args:
                    count_str = args[1: args.index(',')]
                    if count_str in patchedInts:
                        count = patchedInts[count_str]
                    elif count_str.isnumeric():
                        count = int(count_str)
                    else:
                        count = 0
                else:
                    count = int(args[1:-1])
                patchedQuantumRegisters[register] = count

        buggyCircs = {}
        patchedCircs = {}

        for node in astBuggy:
            registerFound = 0
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                funcCall = node.value
                if isinstance(funcCall.func, ast.Name) and funcCall.func.id == 'QuantumCircuit':
                    circ = node.targets[0].id
                    if circ not in buggyCircs:
                        buggyCircs[circ] = {'qubits': 0, 'bits': 0}
                    for arg in funcCall.args:
                        if isinstance(arg, ast.Name):
                            if arg.id in buggyClassicalRegisters: # These lines break when the circuits are initialized with variables holding integers
                                buggyCircs[circ]['bits'] += buggyClassicalRegisters[arg.id]
                                registerFound = 1
                            elif arg.id in buggyInts:
                                buggyCircs[circ]['bits'] = buggyInts[arg.id]
                        if isinstance(arg, ast.Name) and arg.id in buggyQuantumRegisters:
                            buggyCircs[circ]['qubits'] += buggyQuantumRegisters[arg.id]
                            registerFound = 1

                    if registerFound == 0 and len(funcCall.args) > 0:
                        if isinstance(funcCall.args[0], ast.Constant):
                            buggyCircs[circ]['qubits'] += funcCall.args[0].value
                        elif isinstance(funcCall.args[0], ast.Name) and funcCall.args[0].id in buggyInts:
                            buggyCircs[circ]['qubits'] += buggyInts[funcCall.args[0].id]
                        if len(funcCall.args) > 1:
                            if isinstance(funcCall.args[1], ast.Constant):
                                buggyCircs[circ]['bits'] += funcCall.args[1].value
                            elif isinstance(funcCall.args[1], ast.Name) and funcCall.args[1].id in buggyInts:
                                buggyCircs[circ]['bits'] += buggyInts[funcCall.args[1].id]
                    elif len(funcCall.args) == 0:
                        buggyCircs[circ]['qubits'] += 0


        for node in astPatched:
            registerFound = 0
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                funcCall = node.value
                if isinstance(funcCall.func, ast.Name) and funcCall.func.id == 'QuantumCircuit':
                    circ = node.targets[0].id
                    if circ not in patchedCircs:
                        patchedCircs[circ] = {'qubits': 0, 'bits': 0}
                    for arg in funcCall.args:
                        if isinstance(arg, ast.Name) and arg.id in patchedClassicalRegisters:
                            patchedCircs[circ]['bits'] += patchedClassicalRegisters[arg.id]
                            registerFound = 1
                        if isinstance(arg, ast.Name) and arg.id in patchedQuantumRegisters:
                            patchedCircs[circ]['qubits'] += patchedQuantumRegisters[arg.id]
                            registerFound = 1

                    if registerFound == 0:
                        if isinstance(funcCall.args[0], ast.Constant):
                            patchedCircs[circ]['qubits'] += funcCall.args[0].value
                        elif isinstance(funcCall.args[0], ast.Name) and funcCall.args[0].id in patchedInts:
                            patchedCircs[circ]['qubits'] += patchedInts[funcCall.args[0].id]
                        if len(funcCall.args) > 1:
                            if isinstance(funcCall.args[1], ast.Constant):
                                patchedCircs[circ]['bits'] += funcCall.args[1].value
                            elif isinstance(funcCall.args[1], ast.Name) and funcCall.args[1].id in patchedInts:
                                patchedCircs[circ]['bits'] += patchedInts[funcCall.args[1].id]

        for circuit in buggyCircs:
            if circuit in patchedCircs:
                if buggyCircs[circuit]['bits'] != buggyCircs[circuit]['qubits'] and patchedCircs[circuit]['bits'] == patchedCircs[circuit]['qubits']:
                    return True
        return False

    def _detectIncorrectRegisters(self, codeDiff, astSample):
        status = False
        bugTypeMessage = "Unequal bits vs. qubits during QuantumCircuit initialization(s)."
        try:
            status = self._checkIncorrectRegisters(codeDiff, astSample)
            print("checkIncorrectRegisters WORKS")
        except:
            # status = False
            status = True
            print("error in checkIncorrectRegisters")
            raise

        return status, bugTypeMessage
    
    def assessBugType(self, codeSample, astSample):
        return self._detectIncorrectRegisters(codeSample, astSample)