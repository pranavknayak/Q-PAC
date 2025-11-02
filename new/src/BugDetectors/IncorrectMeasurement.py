import numpy as np
import ast
import re

class IncorrectMeasurement():
    def __init__(self):
        # Define gate matrices
        self.gate_matrices = {
            'x': np.array([[0, 1], [1, 0]]),
            'y': np.array([[0, -1j], [1j, 0]]),
            'z': np.array([[1, 0], [0, -1]]),
            'h': np.array([[1, 1], [1, -1]]) / np.sqrt(2),
            's': np.array([[1, 0], [0, 1j]]),
            't': np.array([[1, 0], [0, np.exp(1j * np.pi / 4)]]),
            'sdg': np.array([[1, 0], [0, -1j]]),
            'tdg': np.array([[1, 0], [0, np.exp(-1j * np.pi / 4)]]),
            'id': np.array([[1, 0], [0, 1]]),
            'sx': np.array([[1+1j, 1-1j], [1-1j, 1+1j]]) / 2,
        }
    
    def _getGateMatrix(self, gate_name, params=None):
        """Get the matrix representation of a gate."""
        gate_name = gate_name.lower()
        
        if gate_name in self.gate_matrices:
            return self.gate_matrices[gate_name]
        
        # Parametric gates
        if gate_name == 'rx' and params:
            theta = params[0]
            return np.array([
                [np.cos(theta/2), -1j*np.sin(theta/2)],
                [-1j*np.sin(theta/2), np.cos(theta/2)]
            ])
        elif gate_name == 'ry' and params:
            theta = params[0]
            return np.array([
                [np.cos(theta/2), -np.sin(theta/2)],
                [np.sin(theta/2), np.cos(theta/2)]
            ])
        elif gate_name == 'rz' and params:
            theta = params[0]
            return np.array([
                [np.exp(-1j*theta/2), 0],
                [0, np.exp(1j*theta/2)]
            ])
        elif gate_name == 'p' and params:
            theta = params[0]
            return np.array([[1, 0], [0, np.exp(1j*theta)]])
        
        return np.eye(2)
    
    def _extractGateParams(self, call_node):
        """Extract parameters from gate calls (e.g., rx(pi/2, 0))."""
        params = []
        for arg in call_node.args:
            if isinstance(arg, ast.Constant):
                params.append(arg.value)
            elif isinstance(arg, ast.BinOp):
                try:
                    result = eval(ast.unparse(arg))
                    params.append(result)
                except:
                    params.append(0)
        return params

    def _extractClassicalBitsFromMeasure(self, call_node):
        """Extract classical bit mappings from measure() calls."""
        classical_bits = []
        if len(call_node.args) >= 2:
            # Second argument is the classical bits
            cbits_arg = call_node.args[1]
            if isinstance(cbits_arg, ast.List):
                for elt in cbits_arg.elts:
                    if isinstance(elt, ast.Constant):
                        classical_bits.append(elt.value)
        return classical_bits
    
    def _analyzeQubitOperations(self, code, ast_tree):
        """
        Analyze operations on each qubit, tracking gates and measurements.
        """
        analysis = {}
        circuit_qubits = {}
        current_matrices = {}
        current_gates = {}
        
        # Initialize - find QuantumCircuits and their qubit counts
        for node in ast.walk(ast_tree):
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                if isinstance(node.value.func, ast.Name) and node.value.func.id == "QuantumCircuit":
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            circuit_id = target.id
                            num_qubits = 0
                            
                            if node.value.args and isinstance(node.value.args[0], ast.Constant):
                                num_qubits = node.value.args[0].value
                            elif node.value.args and isinstance(node.value.args[0], ast.Name):
                                reg_name = node.value.args[0].id
                                for n in ast.walk(ast_tree):
                                    if isinstance(n, ast.Assign):
                                        for t in n.targets:
                                            if isinstance(t, ast.Name) and t.id == reg_name:
                                                if isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Name) and n.value.func.id == "QuantumRegister":
                                                    if n.value.args and isinstance(n.value.args[0], ast.Constant):
                                                        num_qubits = n.value.args[0].value
                            
                            if num_qubits > 0:
                                circuit_qubits[circuit_id] = num_qubits
                                analysis[circuit_id] = {}
                                
                                for q in range(num_qubits):
                                    analysis[circuit_id][q] = {
                                        'measurements': [],
                                        'measurement_count': 0
                                    }
                                    current_matrices[(circuit_id, q)] = np.eye(2)
                                    current_gates[(circuit_id, q)] = []
        
        # Process operations using AST walking instead of line-by-line parsing
        self._walkASTForOperations(ast_tree, circuit_qubits, analysis, current_matrices, current_gates)
        
        return analysis
    
    def _walkASTForOperations(self, node, circuit_qubits, analysis, current_matrices, current_gates, in_loop=False):
        """Walk the AST tree to find gate and measurement operations."""
        
        # Check if this is a loop node
        if isinstance(node, (ast.For, ast.While)):
            # Process loop body - mark that we're inside a loop
            for child in ast.iter_child_nodes(node):
                if isinstance(child, list):
                    for item in child:
                        self._walkASTForOperations(item, circuit_qubits, analysis, current_matrices, current_gates, in_loop=True)
                else:
                    self._walkASTForOperations(child, circuit_qubits, analysis, current_matrices, current_gates, in_loop=True)
            return
        
        # Check for measurement or gate operations
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Attribute):
                circuit_name = None
                if isinstance(node.value.func.value, ast.Name):
                    circuit_name = node.value.func.value.id
                
                if circuit_name in circuit_qubits:
                    gate_name = node.value.func.attr
                    
                    # Handle measurement operations
                    if 'measure' in gate_name.lower():
                        qubits = self._extractQubitsFromCall(node.value)
                        classical_bits = self._extractClassicalBitsFromMeasure(node.value)
                        
                        # Handle register variable case
                        if qubits == 'REGISTER':
                            qubits = list(range(circuit_qubits[circuit_name]))
                        
                        if not qubits and circuit_name in circuit_qubits:
                            # measure_all case
                            qubits = list(range(circuit_qubits[circuit_name]))
                            classical_bits = list(range(circuit_qubits[circuit_name]))
                        
                        # If inside a loop, we can't accurately track the accumulated matrix
                        # So we'll only record the measurement once with current gates
                        for i, qubit in enumerate(qubits):
                            if qubit in analysis[circuit_name]:
                                cbit = classical_bits[i] if i < len(classical_bits) else None
                                
                                analysis[circuit_name][qubit]['measurements'].append({
                                    'line': node.lineno,
                                    'matrix': current_matrices[(circuit_name, qubit)].copy(),
                                    'gates': current_gates[(circuit_name, qubit)].copy(),
                                    'classical_bit': cbit,
                                    'in_loop': in_loop
                                })
                                analysis[circuit_name][qubit]['measurement_count'] += 1
                                
                                # Reset after measurement (if not in loop)
                                if not in_loop:
                                    current_matrices[(circuit_name, qubit)] = np.eye(2)
                                    current_gates[(circuit_name, qubit)] = []
                    
                    # Handle gate operations
                    elif gate_name.lower() in self.gate_matrices or gate_name.lower() in ['rx', 'ry', 'rz', 'p']:
                        qubits = self._extractQubitsFromCall(node.value)
                        
                        # Handle register variable for gates too
                        if qubits == 'REGISTER':
                            qubits = list(range(circuit_qubits[circuit_name]))
                        
                        params = self._extractGateParams(node.value)
                        gate_matrix = self._getGateMatrix(gate_name, params)
                        
                        # Only accumulate gates if not inside a loop (to avoid confusion)
                        if not in_loop:
                            for qubit in qubits:
                                if qubit in analysis[circuit_name]:
                                    current_matrices[(circuit_name, qubit)] = gate_matrix @ current_matrices[(circuit_name, qubit)]
                                    current_gates[(circuit_name, qubit)].append((gate_name, node.lineno))
        
        # Recursively walk child nodes
        for child in ast.iter_child_nodes(node):
            self._walkASTForOperations(child, circuit_qubits, analysis, current_matrices, current_gates, in_loop)

    def _extractQubitsFromCall(self, call_node):
        """Extract qubit indices from a gate/measurement call."""
        qubits = []
        
        # For measurement operations, only look at the FIRST argument (quantum qubits)
        # The second argument is classical bits
        if call_node.args:
            first_arg = call_node.args[0]
            
            if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, int):
                qubits.append(first_arg.value)
            elif isinstance(first_arg, ast.List):
                for elt in first_arg.elts:
                    if isinstance(elt, ast.Constant) and isinstance(elt.value, int):
                        qubits.append(elt.value)
            elif isinstance(first_arg, ast.Subscript):
                if isinstance(first_arg.slice, ast.Constant):
                    qubits.append(first_arg.slice.value)
            elif isinstance(first_arg, ast.Name):
                # This is a register variable (e.g., 'q' in measure(q, [0]))
                # We'll return a special marker and handle it in the analysis method
                return 'REGISTER'
            elif isinstance(first_arg, ast.Call):
                # Handle range() calls like x(range(3))
                if isinstance(first_arg.func, ast.Name) and first_arg.func.id == 'range':
                    # Extract the range arguments
                    if first_arg.args:
                        if len(first_arg.args) == 1 and isinstance(first_arg.args[0], ast.Constant):
                            # range(n) -> [0, 1, ..., n-1]
                            n = first_arg.args[0].value
                            qubits = list(range(n))
                        elif len(first_arg.args) == 2:
                            # range(start, stop)
                            if isinstance(first_arg.args[0], ast.Constant) and isinstance(first_arg.args[1], ast.Constant):
                                start = first_arg.args[0].value
                                stop = first_arg.args[1].value
                                qubits = list(range(start, stop))
                        elif len(first_arg.args) == 3:
                            # range(start, stop, step)
                            if all(isinstance(arg, ast.Constant) for arg in first_arg.args):
                                start = first_arg.args[0].value
                                stop = first_arg.args[1].value
                                step = first_arg.args[2].value
                                qubits = list(range(start, stop, step))
        
        return qubits
    
    def _compareMatrices(self, matrix1, matrix2, tolerance=1e-10):
        """Compare two matrices with tolerance for floating point errors."""
        return np.allclose(matrix1, matrix2, atol=tolerance)
    
    def _detectIncorrectMeasurements(self, buggy_analysis, patched_analysis):
        """Detect if measurement is incorrectly placed or has wrong classical bit mappings."""
        incorrect = []
        
        for circuit_id in buggy_analysis:
            if circuit_id not in patched_analysis:
                continue
            
            for qubit in buggy_analysis[circuit_id]:
                if qubit not in patched_analysis[circuit_id]:
                    continue
                
                buggy_count = buggy_analysis[circuit_id][qubit]['measurement_count']
                patched_count = patched_analysis[circuit_id][qubit]['measurement_count']
                
                # Skip if any measurements are inside loops
                buggy_has_loop_measurement = any(m.get('in_loop', False) for m in buggy_analysis[circuit_id][qubit]['measurements'])
                patched_has_loop_measurement = any(m.get('in_loop', False) for m in patched_analysis[circuit_id][qubit]['measurements'])
                
                if buggy_has_loop_measurement or patched_has_loop_measurement:
                    continue
                
                # Check for missing or extra measurements
                if (buggy_count == 0 and patched_count > 0):
                    incorrect.append({
                        'circuit': circuit_id,
                        'qubit': qubit,
                        'measurement_index': 0,
                        'buggy_line': 'N/A',
                        'patched_line': patched_analysis[circuit_id][qubit]['measurements'][0]['line'],
                        'error': f'qubit {qubit} not measured in buggy but measured in patched'
                    })
                    print(f"\nMEASUREMENT BUG: Missing measurement for qubit {qubit} that should be present")
                    continue
                elif (buggy_count > 0 and patched_count == 0):
                    incorrect.append({
                        'circuit': circuit_id,
                        'qubit': qubit,
                        'measurement_index': 0,
                        'buggy_line': buggy_analysis[circuit_id][qubit]['measurements'][0]['line'],
                        'patched_line': 'N/A',
                        'error': f'qubit {qubit} measured in buggy but not in patched'
                    })
                    print(f"\nMEASUREMENT BUG: Extra measurement for qubit {qubit} that should not be present")
                    continue
                
                if buggy_count != patched_count or buggy_count == 0:
                    continue
                
                buggy_measurements = buggy_analysis[circuit_id][qubit]['measurements']
                patched_measurements = patched_analysis[circuit_id][qubit]['measurements']
                
                for i in range(len(buggy_measurements)):
                    buggy_matrix = buggy_measurements[i]['matrix']
                    patched_matrix = patched_measurements[i]['matrix']
                    buggy_cbit = buggy_measurements[i].get('classical_bit')
                    patched_cbit = patched_measurements[i].get('classical_bit')
                    buggy_gates = [g[0] for g in buggy_measurements[i]['gates']]
                    patched_gates = [g[0] for g in patched_measurements[i]['gates']]
                    buggy_line = buggy_measurements[i]['line']
                    patched_line = patched_measurements[i]['line']
                    
                    # Check matrix equality first
                    matrices_same = self._compareMatrices(buggy_matrix, patched_matrix)
                    
                    if matrices_same:
                        # If matrices match but classical bits don't, it's a mapping error
                        if buggy_cbit != patched_cbit:
                            incorrect.append({
                                'circuit': circuit_id,
                                'qubit': qubit,
                                'measurement_index': i,
                                'buggy_line': buggy_line,
                                'patched_line': patched_line,
                                'error': f'wrong classical bit mapping: qubit {qubit} -> cbit {buggy_cbit} (expected {patched_cbit})'
                            })
                            print(f"\nMEASUREMENT BUG: Qubit {qubit} incorrectly mapped to classical bit(s) - check measurement at line {buggy_line}")
                    else:
                        cbits_differ = buggy_cbit != patched_cbit
                        
                        # If measurement line and bits match, it's a gate error not measurement error
                        if buggy_line == patched_line and not cbits_differ:
                            continue
                        
                        if cbits_differ:
                            incorrect.append({
                                'circuit': circuit_id,
                                'qubit': qubit,
                                'measurement_index': i,
                                'buggy_line': buggy_line,
                                'patched_line': patched_line,
                                'error': f'wrong classical bit mapping: qubit {qubit} -> cbit {buggy_cbit} (expected {patched_cbit})'
                            })
                            print(f"\nMEASUREMENT BUG: Qubit {qubit} mapped to wrong classical bit(s) at line {buggy_line}")
                        else:
                            # Check if measurement timing is wrong
                            buggy_is_prefix = (len(buggy_gates) < len(patched_gates) and 
                                            patched_gates[:len(buggy_gates)] == buggy_gates)
                            patched_is_prefix = (len(patched_gates) < len(buggy_gates) and 
                                                buggy_gates[:len(patched_gates)] == patched_gates)
                            
                            if buggy_is_prefix:
                                incorrect.append({
                                    'circuit': circuit_id,
                                    'qubit': qubit,
                                    'measurement_index': i,
                                    'buggy_line': buggy_line,
                                    'patched_line': patched_line,
                                    'error': f'measurement too early: after {buggy_gates} instead of {patched_gates}'
                                })
                                print(f"\nMEASUREMENT BUG: Qubit {qubit} measured too early at line {buggy_line}")
                            elif patched_is_prefix:
                                incorrect.append({
                                    'circuit': circuit_id,
                                    'qubit': qubit,
                                    'measurement_index': i,
                                    'buggy_line': buggy_line,
                                    'patched_line': patched_line,
                                    'error': f'measurement too late: after {buggy_gates} instead of {patched_gates}'
                                })
                                print(f"\nMEASUREMENT BUG: Qubit {qubit} measured too late at line {buggy_line}")
        
        return incorrect

    def _detectIncorrectMeasurement(self, codeSample, astSample):
        result = {
            'IncorrectMeasurement': 'None'
        }
        
        try:
            buggy, patched = codeSample[0], codeSample[1]
            astBuggy, astPatched = astSample[0], astSample[1]

            buggy_analysis = self._analyzeQubitOperations(buggy, astBuggy)
            patched_analysis = self._analyzeQubitOperations(patched, astPatched)
            
            incorrect = self._detectIncorrectMeasurements(buggy_analysis, patched_analysis)
            
            if incorrect:
                messages = []
                for item in incorrect:
                    messages.append(
                        f"Circuit '{item['circuit']}', qubit {item['qubit']} at line {item['buggy_line']}: {item['error']}"
                    )
                result['IncorrectMeasurement'] = '; '.join(messages)
            
        except Exception as e:
            print(f"Error in detectIncorrectMeasurement: {e}")
            import traceback
            traceback.print_exc()
        
        return result

    def assessBugType(self, codeSample, astSample):
        result = self._detectIncorrectMeasurement(codeSample, astSample)
        has_bug = result['IncorrectMeasurement'] != 'None'
        return has_bug, result