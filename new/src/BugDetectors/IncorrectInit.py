import ast
import re
import numpy as np
from safeEval import safeEval

class IncorrectInit():
    def _returnArgs(self, args):
        args = "".join(args.split(" "))
        square = []
        paren = []
        value = ""
        parenCheck = 0
        subparencheck = 0
        squareCheck = 0

        for char in args:
            if char == "(":
                if parenCheck == 1:
                    subparencheck = 1
                    value += char
                else:
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
                if subparencheck == 1:
                    subparencheck = 0
                    value += char
                else:
                    parenCheck = 0
                    if len(value) > 0:
                        paren.append(value)
            elif char == ",":
                if parenCheck and value != "":
                    if squareCheck:
                        square.append(value)
                    elif subparencheck:
                        subparen += (value,)
                    else:
                        paren.append(value)
                value = ""
            else:
                value += char

        for args in range(len(paren)):
            if isinstance(paren[args], list):
                for index in range(len(paren[args])):
                    try:
                        paren[args][index] = safeEval(paren[args][index], {})
                    except NameError:
                        continue
            else:
                try:
                    paren[args] = safeEval(paren[args], {})
                except NameError:
                    continue

        return np.array(paren)


    def _checkIncorrectParam(self, codeSample, astSample):
        regex1 = ".+\..*"
        regex2 = ".+QuantumCircuit.*"
        availableInbuiltGates = [
            "ccx",
            "cx",
            "cz",
            "cy",
            # "h",
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
        ]

        buggy, patched = codeSample[0], codeSample[1]
        buggyID, patchedID = {}, {}
        buggyList = list(filter(("").__ne__, buggy.split("\n")))
        patchedList = list(filter(("").__ne__, patched.split("\n")))
        buggyGate, patchedGate = {}, {}
        buggyQuantum, patchedQuantum = {}, {}
        # astBuggy, astPatched = ast.walk(ast.parse(buggy)), ast.walk(ast.parse(patched))
        astBuggy, astPatched = ast.walk(astSample[0]), ast.walk(astSample[1])
        buggyRegs, patchedRegs = {}, {}
        buggy_int_vals, patched_int_vals = {}, {}

        """ Retrieves all instances of a QuantumCircuit object in both, the buggy and patched codes."""
        for node in astBuggy:
            if isinstance(node, ast.Assign):
                for id in getattr(node, "targets"):
                    if isinstance(node.value, ast.Constant):
                        buggy_int_vals[id.id] = node.value.value
                    elif (
                        id.id not in buggyID
                        and isinstance(node.value, ast.Call)
                        and isinstance(node.value.func, ast.Name)
                        and getattr(node, "value").func.id == "QuantumCircuit"
                    ):
                        args = node.value.args
                        if isinstance(args[0], ast.Constant):
                            qubits = args[0].value
                        elif isinstance(args[0], ast.Name):
                            if args[0].id in buggyRegs:
                                qubits = buggyRegs[args[0].id]
                            elif args[0].id in buggy_int_vals:
                                qubits = buggy_int_vals[args[0].id]
                            else:
                                qubits = 0
                        else:
                            qubits = 0
                        buggyID[id.id] = [0] * qubits
                    elif (
                        id.id not in buggyRegs
                        and isinstance(node.value, ast.Call)
                        and isinstance(node.value.func, ast.Name)
                        and node.value.func.id == "QuantumRegister"
                    ):
                        if isinstance(node.value.args[0], ast.Name):
                            buggyRegs[id.id] = buggy_int_vals.get(node.value.args[0].id, 0)
                        else:
                            buggyRegs[id.id] = node.value.args[0].value

        for node in astPatched:
            if isinstance(node, ast.Assign):
                for id in getattr(node, "targets"):
                    if isinstance(node.value, ast.Constant):
                        patched_int_vals[id.id] = node.value.value
                    elif (
                        id.id not in patchedID
                        and isinstance(node.value, ast.Call)
                        and isinstance(node.value.func, ast.Name)
                        and getattr(node, "value").func.id == "QuantumCircuit"
                    ):
                        args = node.value.args
                        if isinstance(args[0], ast.Constant):
                            qubits = args[0].value
                        elif isinstance(args[0], ast.Name):
                            if args[0].id in patchedRegs:
                                qubits = patchedRegs[args[0].id]
                            elif args[0].id in patched_int_vals:
                                qubits = patched_int_vals[args[0].id]
                            else:
                                qubits = 0
                        else:
                            qubits = 0

                        patchedID[id.id] = [0] * qubits
                    elif (
                        id.id not in patchedRegs
                        and isinstance(node.value, ast.Call)
                        and isinstance(node.value.func, ast.Name)
                        and node.value.func.id == "QuantumRegister"
                    ):
                        if isinstance(node.value.args[0], ast.Name):
                            patchedRegs[id.id] = patched_int_vals.get(node.value.args[0].id, 0)
                        else:
                            patchedRegs[id.id] = node.value.args[0].value

        # Do NOT treat differing counts of circuits as IncorrectInit here.
        # Excess / missing circuits/gates will be handled by other detectors (IncorrectStandardGate / IncorrectOpaqueGate).
        # Proceed with argument checks only for circuits/gates present in BOTH versions.

        """ Deduces if the arguments are amongst the possible arguments for an inbuilt
            gate operation in Qiskit, in both codes.
        """

        # helper to normalize register-index notation (e.g. q[0] -> 0) using known registers
        def _normalize_register_indices(arg_str, known_regs):
            def _repl(m):
                reg = m.group(1)
                idx = m.group(2)
                if reg in known_regs:
                    return idx
                return m.group(0)
            return re.sub(r"([A-Za-z_]\w*)\s*\[\s*(\d+)\s*\]", _repl, arg_str)

        for line in buggyList:
            temporaryStatus = re.search(regex1, line)
            if temporaryStatus is not None:
                parts = line.split(".")
                if len(parts) < 2:
                    continue
                gate = parts[1].split("(")[0].strip().lower()  # normalize
                if gate in availableInbuiltGates:
                    args = line.split(gate)[1]
                    args = _normalize_register_indices(args, buggyRegs)
                    if gate not in buggyGate:
                        buggyGate[gate] = np.array([self._returnArgs(args)])
                    else:
                        buggyGate[gate] = np.append(buggyGate[gate], self._returnArgs(args))

        for line in patchedList:
            temporaryStatus = re.search(regex1, line)
            if temporaryStatus is not None:
                parts = line.split(".")
                if len(parts) < 2:
                    continue
                gate = parts[1].split("(")[0].strip().lower()  # normalize
                if gate in availableInbuiltGates:
                    args = line.split(gate)[1]
                    args = _normalize_register_indices(args, patchedRegs)
                    if gate not in patchedGate:
                        patchedGate[gate] = np.array([self._returnArgs(args)])
                    else:
                        patchedGate[gate] = np.append(patchedGate[gate], self._returnArgs(args))

        # Only consider gates that appear in BOTH versions (ignore excess/missing gates)
        common_gates = set(buggyGate.keys()) & set(patchedGate.keys())
        buggyGate = {g: buggyGate[g] for g in common_gates}
        patchedGate = {g: patchedGate[g] for g in common_gates}
        # ------------------------------------------------------------------------------

        """ Checks if the arguments are amongst the possible arguments for a QuantumCircuit
            object in both codes.
        """
        for line in buggyList:
            temporaryStatus = re.search(regex2, line)
            if temporaryStatus is not None:
                # use circuit variable name as the key instead of the whole line
                if "=" in line:
                    circ_name = line.split("=")[0].strip()
                else:
                    circ_name = line.strip()
                args = line.split("QuantumCircuit")[1]
                args = _normalize_register_indices(args, buggyRegs)
                buggyQuantum[circ_name] = self._returnArgs(args)

        for line in patchedList:
            temporaryStatus = re.search(regex2, line)
            if temporaryStatus is not None:
                if "=" in line:
                    circ_name = line.split("=")[0].strip()
                else:
                    circ_name = line.strip()
                args = line.split("QuantumCircuit")[1]
                args = _normalize_register_indices(args, patchedRegs)
                patchedQuantum[circ_name] = self._returnArgs(args)

        buggyGateValue, patchedGateValue = list(buggyGate.values()), list(
            patchedGate.values()
        )
        buggyQuantumValue, patchedQuantumValue = list(buggyQuantum.values()), list(
            patchedQuantum.values()
        )

        # helper: normalize rows for comparison
        def _rows(x):
            try:
                arr = np.asarray(x)
                if arr.ndim == 1:
                    return [arr]
                return [arr[i] for i in range(arr.shape[0])]
            except Exception:
                return [np.asarray(x)]

        # helper: tolerant equality for arg-vectors
        def _args_equal(a, b):
            try:
                if np.array_equal(np.asarray(a), np.asarray(b)):
                    return True
            except Exception:
                pass
            try:
                sa = list(map(str, np.asarray(a).flatten()))
                sb = list(map(str, np.asarray(b).flatten()))
                return set(sa) == set(sb)
            except Exception:
                return False

        # Compare circuit init args only for circuits present in both versions
        common_quantums = set(buggyQuantum.keys()) & set(patchedQuantum.keys())
        for quantum in common_quantums:
            if not _args_equal(buggyQuantum[quantum], patchedQuantum[quantum]):
                return True

        # Compare gate argument vectors only for gates present in BOTH versions (common_gates)
        for gate in buggyGate.keys():  # buggyGate already restricted to common_gates
            buggy_rows = _rows(buggyGate[gate])
            patched_rows = _rows(patchedGate[gate])
            # every buggy row must have a matching patched row (order-insensitive)
            for br in buggy_rows:
                if not any(_args_equal(br, pr) for pr in patched_rows):
                    return True
            # and every patched row must have a matching buggy row
            for pr in patched_rows:
                if not any(_args_equal(pr, br) for br in buggy_rows):
                    return True

        return False

    def _detectIncorrectInit(self, codeDiff, astSample):
        status = False
        bugTypeMessage = "Incorrect initialization(s) attempted."
        try:
            status = self._checkIncorrectParam(codeDiff, astSample)
            print("checkIncorrectParam WORKS")
        except:
            status = False
            # status = True
            print("error in checkIncorrectParam")
            raise
        return status, bugTypeMessage

    def assessBugType(self, codeSample, astSample):
        return self._detectIncorrectInit(codeSample, astSample)