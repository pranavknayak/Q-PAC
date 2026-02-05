import ast
import re
import numpy as np
from collections import defaultdict
from safeEval import safeEval

class IncorrectHadamard():
    def _extractIters(self, node: ast.For):
        target = ast.Name(node.target)
        target_id = target.id
        if isinstance(node.iter, ast.Call):
            return ast.Constant(node.iter.args[0]).value
        elif isinstance(node.iter, ast.List):
            return len(node.iter.elts)
    def _checkHadamard(self, codeDiff, astSample):
        qubitRegex = r"\.h\(.*\)"
        circuitRegex = r".+\.h"

        buggy_int_vals, patched_int_vals = {}, {}
        buggy, patched = codeDiff[0], codeDiff[1]
        buggyRegs, patchedRegs = {}, {}
        buggyList = list(filter(("").__ne__, buggy.split("\n")))
        patchedList = list(filter(("").__ne__, patched.split("\n")))

        containsHadamard = 0
        for line in buggyList + patchedList:
            present = re.search(qubitRegex, line)
            if present is not None:
                containsHadamard += 1
        if containsHadamard == 0:
            return False

        buggyAST, patchedAST = ast.walk(astSample[0]), ast.walk(astSample[1])

        # Store circuits with their qubit counts and order
        buggy_circuits = []
        patched_circuits = []

        for node in buggyAST:
            if isinstance(node, ast.Assign):
                for id in getattr(node, "targets"):
                    if isinstance(node.value, ast.Constant):
                        buggy_int_vals[id.id] = node.value.value
                    elif (
                        isinstance(node.value, ast.Call)
                        and isinstance(node.value.func, ast.Name)
                        and node.value.func.id == "QuantumRegister"
                    ):
                        if isinstance(node.value.args[0], ast.Name):
                            buggyRegs[id.id] = buggy_int_vals[node.value.args[0].id]
                        else:
                            buggyRegs[id.id] = node.value.args[0].value
                    elif (
                        isinstance(node.value, ast.Call)
                        and isinstance(node.value.func, ast.Name)
                        and node.value.func.id == "QuantumCircuit"
                    ):
                        qubits = 0
                        args = node.value.args
                        if isinstance(args[0], ast.Constant):
                            qubits = args[0].value
                        elif isinstance(args[0], ast.Name):
                            if args[0].id in buggyRegs:
                                qubits = buggyRegs[args[0].id]
                            elif args[0].id in buggy_int_vals:
                                qubits = buggy_int_vals[args[0].id]
                        buggy_circuits.append((id.id, qubits))

        for node in patchedAST:
            if isinstance(node, ast.Assign):
                for id in getattr(node, "targets"):
                    if isinstance(node.value, ast.Constant):
                        patched_int_vals[id.id] = node.value.value
                    elif (
                        isinstance(node.value, ast.Call)
                        and isinstance(node.value.func, ast.Name)
                        and node.value.func.id == "QuantumRegister"
                    ):
                        if isinstance(node.value.args[0], ast.Name):
                            patchedRegs[id.id] = patched_int_vals[node.value.args[0].id]
                        else:
                            patchedRegs[id.id] = node.value.args[0].value
                    elif (
                        isinstance(node.value, ast.Call)
                        and isinstance(node.value.func, ast.Name)
                        and node.value.func.id == "QuantumCircuit"
                    ):
                        qubits = 0
                        args = node.value.args
                        if isinstance(args[0], ast.Constant):
                            qubits = args[0].value
                        elif isinstance(args[0], ast.Name):
                            if args[0].id in patchedRegs:
                                qubits = patchedRegs[args[0].id]
                            elif args[0].id in patched_int_vals:
                                qubits = patched_int_vals[args[0].id]
                        patched_circuits.append((id.id, qubits))

        # Initialize Hadamard counts for each circuit
        buggyID = {}
        patchedID = {}
        
        for circ_name, num_qubits in buggy_circuits:
            buggyID[circ_name] = {i: 0 for i in range(num_qubits)}
        
        for circ_name, num_qubits in patched_circuits:
            patchedID[circ_name] = {i: 0 for i in range(num_qubits)}

        # Count Hadamard gates in buggy code
        for line in buggyList:
            qbit_result = re.search(qubitRegex, line)
            if qbit_result is None:
                continue

            qubit_arg = qbit_result.group()[3:-1].strip()
            indices = []
            full_reg = False

            if qubit_arg.startswith("[") and qubit_arg.endswith("]"):
                inner = qubit_arg[1:-1]
                for part in inner.split(","):
                    part = part.strip()
                    try:
                        indices.append(int(safeEval(part, buggy_int_vals)))
                    except:
                        if part.isdigit():
                            indices.append(int(part))
            elif qubit_arg.isdigit():
                indices.append(int(qubit_arg))
            else:
                # Try to evaluate as expression first (e.g., 0+1, 2-1, etc.)
                try:
                    idx = int(safeEval(qubit_arg, buggy_int_vals))
                    indices.append(idx)
                except:
                    # Check for register indexing like q[0]
                    m = re.match(r".*\[(\d+)\].*", qubit_arg)
                    if m:
                        indices.append(int(m.group(1)))
                    else:
                        full_reg = True

            circ_result = re.search(circuitRegex, line)
            if circ_result is None:
                continue
            circ_id = circ_result.group()[:-2].strip()

            if circ_id not in buggyID:
                continue

            if full_reg:
                for i in buggyID[circ_id].keys():
                    buggyID[circ_id][i] += 1
            else:
                for idx in indices:
                    if idx in buggyID[circ_id]:
                        buggyID[circ_id][idx] += 1

        # Count Hadamard gates in patched code
        for line in patchedList:
            qbit_result = re.search(qubitRegex, line)
            if qbit_result is None:
                continue

            qubit_arg = qbit_result.group()[3:-1].strip()
            indices = []
            full_reg = False

            if qubit_arg.startswith("[") and qubit_arg.endswith("]"):
                inner = qubit_arg[1:-1]
                for part in inner.split(","):
                    part = part.strip()
                    try:
                        indices.append(int(safeEval(part, patched_int_vals)))
                    except:
                        if part.isdigit():
                            indices.append(int(part))
            elif qubit_arg.isdigit():
                indices.append(int(qubit_arg))
            else:
                # Try to evaluate as expression first (e.g., 0+1, 2-1, etc.)
                try:
                    idx = int(safeEval(qubit_arg, patched_int_vals))
                    indices.append(idx)
                except:
                    # Check for register indexing like q[0]
                    m = re.match(r".*\[(\d+)\].*", qubit_arg)
                    if m:
                        indices.append(int(m.group(1)))
                    else:
                        full_reg = True

            circ_result = re.search(circuitRegex, line)
            if circ_result is None:
                continue
            circ_id = circ_result.group()[:-2].strip()

            if circ_id not in patchedID:
                continue

            if full_reg:
                for i in patchedID[circ_id].keys():
                    patchedID[circ_id][i] += 1
            else:
                for idx in indices:
                    if idx in patchedID[circ_id]:
                        patchedID[circ_id][idx] += 1

        # Compare circuits by their ORDER and structure, not by name
        for i in range(min(len(buggy_circuits), len(patched_circuits))):
            buggy_circ_name, buggy_num_qubits = buggy_circuits[i]
            patched_circ_name, patched_num_qubits = patched_circuits[i]
            
            if buggy_num_qubits != patched_num_qubits:
                continue
            
            for qubit_idx in range(min(len(buggyID[buggy_circ_name]), len(patchedID[patched_circ_name]))):
                buggy_h_count = buggyID[buggy_circ_name].get(qubit_idx, 0)
                patched_h_count = patchedID[patched_circ_name].get(qubit_idx, 0)
                
                if (buggy_h_count + patched_h_count) % 2 != 0:
                    # Single clear print statement explaining why we detected IncorrectHadamard
                    print(f"\nHADAMARD BUG: Qubit {qubit_idx} has {buggy_h_count} H gates in buggy version and {patched_h_count} H gates in fixed version (total {buggy_h_count + patched_h_count} is odd)")
                    return True
        
        return False

    def _detectIncorrectHadamard(self, codeDiff, astSample):
        status = False
        bugTypeMessage = "Unclosed Hadamard gate detected."
        try:
            status = self._checkHadamard(codeDiff, astSample)
        except:
            status = False
            raise

        return status, bugTypeMessage

    def assessBugType(self, codeSample, astSample):
        return self._detectIncorrectHadamard(codeSample, astSample)