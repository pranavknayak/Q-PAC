import ast
import re

class ExcessiveMeasurements():
    def __init__(self):
        pass
    
    def _analyzeQubitMeasurements(self, code, ast_tree):
        """
        Analyze measurement operations on each qubit, accounting for loops.
        Returns: {
            circuit_id: {
                qubit_idx: {
                    'measurement_count': int,
                    'measurement_lines': [line_numbers]
                }
            }
        }
        """
        analysis = {}
        circuit_qubits = {}
        register_sizes = {}
        
        # First pass: find QuantumRegister definitions
        for node in ast.walk(ast_tree):
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                if isinstance(node.value.func, ast.Name) and node.value.func.id == "QuantumRegister":
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            reg_name = target.id
                            if node.value.args and isinstance(node.value.args[0], ast.Constant):
                                register_sizes[reg_name] = node.value.args[0].value
        
        # Second pass: find QuantumCircuit definitions
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
                                num_qubits = register_sizes.get(reg_name, 0)
                            
                            if num_qubits > 0:
                                circuit_qubits[circuit_id] = num_qubits
                                analysis[circuit_id] = {}
                                for q in range(num_qubits):
                                    analysis[circuit_id][q] = {
                                        'measurement_count': 0,
                                        'measurement_lines': []
                                    }
        
        # Third pass: analyze measurements with loop detection
        self._analyzeMeasurementsWithLoops(ast_tree, circuit_qubits, analysis)
        
        return analysis
    
    def _analyzeMeasurementsWithLoops(self, ast_tree, circuit_qubits, analysis):
        """Recursively analyze measurements, accounting for loops."""
        self._walkNodeWithLoopContext(ast_tree, circuit_qubits, analysis, loop_multiplier=1)

    def _walkNodeWithLoopContext(self, node, circuit_qubits, analysis, loop_multiplier=1):
        """Walk AST nodes and track loop iterations."""
        if isinstance(node, ast.For):
            # Detect loop iterations
            iter_count = 1
            if isinstance(node.iter, ast.Call):
                if isinstance(node.iter.func, ast.Name) and node.iter.func.id == 'range':
                    # Extract range value
                    if node.iter.args and isinstance(node.iter.args[0], ast.Constant):
                        iter_count = node.iter.args[0].value
            
            print(f"DEBUG: Found for loop with {iter_count} iterations, current multiplier: {loop_multiplier}")
            
            # Process loop body with increased multiplier
            for child in node.body:
                self._walkNodeWithLoopContext(child, circuit_qubits, analysis, loop_multiplier * iter_count)
            
            # Don't continue walking this node's children since we already processed the body
            return
        
        elif isinstance(node, ast.While):
            # For while loops, we can't determine iterations statically
            # Assume at least 1 iteration (conservative estimate)
            for child in node.body:
                self._walkNodeWithLoopContext(child, circuit_qubits, analysis, loop_multiplier)
            return
        
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            # Check if it's a measurement call
            if isinstance(node.value.func, ast.Attribute):
                circuit_name = None
                if isinstance(node.value.func.value, ast.Name):
                    circuit_name = node.value.func.value.id
                
                if circuit_name in circuit_qubits:
                    gate_name = node.value.func.attr
                    
                    if 'measure' in gate_name.lower():
                        qubits = self._extractQubitsFromCall(node.value)
                        
                        print(f"DEBUG: Found measurement at line {node.lineno}, qubits: {qubits}, multiplier: {loop_multiplier}")
                        
                        if not qubits:
                            qubits = list(range(circuit_qubits[circuit_name]))
                        
                        for qubit in qubits:
                            if qubit in analysis[circuit_name]:
                                analysis[circuit_name][qubit]['measurement_count'] += loop_multiplier
                                if node.lineno not in analysis[circuit_name][qubit]['measurement_lines']:
                                    analysis[circuit_name][qubit]['measurement_lines'].append(node.lineno)
                                print(f"  DEBUG: Qubit {qubit} now has {analysis[circuit_name][qubit]['measurement_count']} measurements")
        
        # Recursively walk child nodes (but NOT for loops, we handled those above)
        for child in ast.iter_child_nodes(node):
            self._walkNodeWithLoopContext(child, circuit_qubits, analysis, loop_multiplier)

    def _extractQubitsFromCall(self, call_node):
        """Extract qubit indices from a gate/measurement call."""
        qubits = []
        
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
        
        return qubits

    def _detectExcessiveMeasurements(self, buggy_analysis, patched_analysis):
        """Detect if any qubit is measured excessively in buggy code."""
        excessive = []
        
        for circuit_id in buggy_analysis:
            if circuit_id not in patched_analysis:
                continue
            
            for qubit in buggy_analysis[circuit_id]:
                if qubit not in patched_analysis[circuit_id]:
                    continue
                
                buggy_count = buggy_analysis[circuit_id][qubit]['measurement_count']
                patched_count = patched_analysis[circuit_id].get(qubit, {}).get('measurement_count', 0)
                
                if buggy_count > patched_count:
                    buggy_lines = buggy_analysis[circuit_id][qubit]['measurement_lines']
                    patched_lines = patched_analysis[circuit_id][qubit].get('measurement_lines', [])
                    
                    excessive.append({
                        'circuit': circuit_id,
                        'qubit': qubit,
                        'buggy_count': buggy_count,
                        'patched_count': patched_count,
                        'buggy_lines': buggy_lines,
                        'patched_lines': patched_lines
                    })
        
        return excessive
    
    def _detectExcessiveMeasurement(self, codeSample, astSample):
        result = {
            'ExcessiveMeasurements': 'None'
        }
        
        try:
            print("\n=== ExcessiveMeasurements Analysis ===")
            buggy, patched = codeSample[0], codeSample[1]
            astBuggy, astPatched = astSample[0], astSample[1]
            
            buggy_analysis = self._analyzeQubitMeasurements(buggy, astBuggy)
            patched_analysis = self._analyzeQubitMeasurements(patched, astPatched)
            
            print(f"Buggy analysis: {buggy_analysis}")
            print(f"Patched analysis: {patched_analysis}")
            
            excessive = self._detectExcessiveMeasurements(buggy_analysis, patched_analysis)
            
            print(f"Excessive measurements found: {len(excessive)}")
            print(f"Details: {excessive}")
            
            if excessive:
                messages = []
                for item in excessive:
                    messages.append(
                        f"Circuit '{item['circuit']}', qubit {item['qubit']}: "
                        f"measured {item['buggy_count']} times at lines {item['buggy_lines']} "
                        f"(expected {item['patched_count']} times at lines {item['patched_lines']})"
                    )
                result['ExcessiveMeasurements'] = '; '.join(messages)
            
            print(f"Final result: {result}")
            print("=== End ExcessiveMeasurements Analysis ===\n")
            
        except Exception as e:
            print(f"Error in detectExcessiveMeasurement: {e}")
            import traceback
            traceback.print_exc()
        
        return result

    def assessBugType(self, codeSample, astSample):
        result = self._detectExcessiveMeasurement(codeSample, astSample)
        has_bug = result['ExcessiveMeasurements'] != 'None'
        return has_bug, result