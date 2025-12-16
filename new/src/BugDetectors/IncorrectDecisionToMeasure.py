import ast 
import re


class IncorrectDecisionToMeasure():
    
    def _identifyCircuitListVariables(self, ast_tree):
        circuit_list_vars = set()
        circuit_vars = set()
        
        # First pass: identify individual circuit variables (NOT lists or comprehensions)
        for node in ast.walk(ast_tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        # Skip if it's a list or list comprehension
                        if isinstance(node.value, (ast.List, ast.ListComp)):
                            continue
                        if self._containsQuantumCircuitCall(node.value):
                            circuit_vars.add(target.id)
                            print(f"Found individual circuit variable: {target.id}")
        
        print(f"All individual circuit variables: {circuit_vars}")
        
        # Second pass: identify lists of circuits
        for node in ast.walk(ast_tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if isinstance(node.value, ast.ListComp):
                            if self._containsQuantumCircuitCall(node.value.elt):
                                circuit_list_vars.add(target.id)
                                print(f"Found circuit list (comprehension): {target.id}")
                        
                        elif isinstance(node.value, ast.List) and len(node.value.elts) > 0:
                            has_circuit_call = False
                            has_circuit_var = False
                            
                            for elt in node.value.elts:
                                if self._containsQuantumCircuitCall(elt):
                                    has_circuit_call = True
                                    break
                                if isinstance(elt, ast.Name) and elt.id in circuit_vars:
                                    has_circuit_var = True
                            
                            if has_circuit_call or has_circuit_var:
                                circuit_list_vars.add(target.id)
                                print(f"Found circuit list (literal): {target.id}")
                        
                        elif isinstance(node.value, ast.List) and len(node.value.elts) == 0:
                            var_name = target.id
                            print(f"Found empty list: {var_name}, checking for appends...")
                            if self._hasCircuitAppends(ast_tree, var_name, circuit_vars):
                                circuit_list_vars.add(var_name)
                                print(f"Found circuit list (empty+append): {var_name}")
                            else:
                                print(f"No circuit appends found for {var_name}")
                        
                        elif isinstance(node.value, ast.Call):
                            if self._isCircuitReturningFunction(node.value):
                                circuit_list_vars.add(target.id)
                                print(f"Found circuit list (function): {target.id}")
            
            elif isinstance(node, ast.For):
                for child in ast.walk(node):
                    if isinstance(child, ast.Expr) and isinstance(child.value, ast.Call):
                        if (isinstance(child.value.func, ast.Attribute) and 
                            child.value.func.attr == 'append'):
                            if isinstance(child.value.func.value, ast.Name):
                                var_name = child.value.func.value.id
                                if child.value.args:
                                    if self._containsQuantumCircuitCall(child.value.args[0]):
                                        circuit_list_vars.add(var_name)
                                        print(f"Found circuit list (loop append): {var_name}")
        
        print(f"Final circuit list variables: {circuit_list_vars}")
        return circuit_list_vars
    
    def _containsQuantumCircuitCall(self, node):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == 'QuantumCircuit':
                return True
            if isinstance(node.func, ast.Attribute) and node.func.attr == 'QuantumCircuit':
                return True
        
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name) and child.func.id == 'QuantumCircuit':
                    return True
                if isinstance(child.func, ast.Attribute) and child.func.attr == 'QuantumCircuit':
                    return True
        return False
    
    def _hasCircuitAppends(self, ast_tree, var_name, circuit_vars):
        print(f"  Checking for appends to: {var_name}")
        for node in ast.walk(ast_tree):
            # Check for Call nodes with append attribute
            if isinstance(node, ast.Call):
                if (isinstance(node.func, ast.Attribute) and 
                    node.func.attr == 'append'):
                    if isinstance(node.func.value, ast.Name):
                        if node.func.value.id == var_name:
                            print(f"    Found append call to {var_name}")
                            if node.args:
                                arg = node.args[0]
                                print(f"    Arg type: {type(arg).__name__}")
                                
                                # Check if arg is a QuantumCircuit call
                                if self._containsQuantumCircuitCall(arg):
                                    print(f"    YES! Contains QuantumCircuit call")
                                    return True
                                
                                # Check if arg is a circuit variable
                                if isinstance(arg, ast.Name) and arg.id in circuit_vars:
                                    print(f"    YES! Arg '{arg.id}' is a circuit variable")
                                    return True
                                
                                print(f"    Arg is neither QuantumCircuit call nor circuit variable")
        print(f"  No circuit appends found")
        return False
    
    def _isCircuitReturningFunction(self, call_node):
        func_names_that_return_circuits = [
            'construct_circuits', 'build_circuits', 'create_circuits',
            'make_circuits', 'generate_circuits'
        ]
        
        if isinstance(call_node.func, ast.Attribute):
            if call_node.func.attr in func_names_that_return_circuits:
                return True
        elif isinstance(call_node.func, ast.Name):
            if call_node.func.id in func_names_that_return_circuits:
                return True
        
        return False
    
    def _isCircuitListVariable(self, var_name, circuit_list_vars):
        if var_name in circuit_list_vars:
            return True
        
        for circuit_var in circuit_list_vars:
            if circuit_var in var_name:
                return True
        
        return False
    
    def _checkBinRepCalls(self, code_ast):
        binrep_call = []
        for node in code_ast:
            if (
                isinstance(node, ast.Call) and
                isinstance(node.func, ast.Attribute) and
                isinstance(node.func.value, ast.Name)
            ):
                if (
                    node.func.value.id == "np" and
                    node.func.attr == "binary_repr"
                ):  
                    binrep_call.append(node.args)  
                
        return binrep_call

    def _extractSubscriptInfo(self, node, circuit_list_vars):
        if not isinstance(node, ast.Subscript):
            return None
        
        value_repr = ast.dump(node.value)
        
        if isinstance(node.value, ast.Name):
            if not self._isCircuitListVariable(node.value.id, circuit_list_vars):
                return None
        elif isinstance(node.value, ast.Attribute):
            attr_name = self._getAttributeName(node.value)
            if not self._isCircuitListVariable(attr_name, circuit_list_vars):
                result_attrs = ['quasi_dists', 'measurements', 'results', 'data', 'shots_list']
                is_result_attr = any(attr in attr_name for attr in result_attrs)
                if not is_result_attr:
                    return None
        else:
            return None
        
        if isinstance(node.slice, ast.Name):
            index_repr = node.slice.id
            slice_type = 'name'
        elif isinstance(node.slice, ast.Constant):
            index_repr = str(node.slice.value)
            slice_type = 'constant'
        elif isinstance(node.slice, ast.Slice):
            index_repr = ast.dump(node.slice)
            slice_type = 'slice'
        elif isinstance(node.slice, ast.Index):
            if isinstance(node.slice.value, ast.Name):
                index_repr = node.slice.value.id
                slice_type = 'name'
            elif isinstance(node.slice.value, ast.Constant):
                index_repr = str(node.slice.value.value)
                slice_type = 'constant'
            else:
                index_repr = ast.dump(node.slice.value)
                slice_type = 'other'
        elif isinstance(node.slice, ast.BinOp):
            index_repr = ast.dump(node.slice)
            slice_type = 'binop'
        else:
            index_repr = ast.dump(node.slice)
            slice_type = 'other'
        
        return {'value': value_repr, 'index': index_repr, 'slice_type': slice_type}
    
    def _getAttributeName(self, node):
        if isinstance(node, ast.Attribute):
            return self._getAttributeName(node.value) + '.' + node.attr
        elif isinstance(node, ast.Name):
            return node.id
        return ''

    def _checkLoopIndexUsage(self, code_ast, circuit_list_vars):
        loop_info = []
        
        for node in code_ast:
            if isinstance(node, ast.For):
                loop_vars = []
                if isinstance(node.target, ast.Name):
                    loop_vars.append(node.target.id)
                elif isinstance(node.target, ast.Tuple):
                    for n in node.target.elts:
                        if isinstance(n, ast.Name):
                            loop_vars.append(n.id)
                
                iter_dump = ast.dump(node.iter)
                
                is_circuit_loop = False
                if isinstance(node.iter, ast.Name):
                    if self._isCircuitListVariable(node.iter.id, circuit_list_vars):
                        is_circuit_loop = True
                elif isinstance(node.iter, ast.Call):
                    if node.iter.args:
                        first_arg = node.iter.args[0]
                        if isinstance(first_arg, ast.Name):
                            if self._isCircuitListVariable(first_arg.id, circuit_list_vars):
                                is_circuit_loop = True
                
                if not is_circuit_loop:
                    continue
                
                subscripts = []
                for child in ast.walk(node):
                    if isinstance(child, ast.Subscript):
                        sub_info = self._extractSubscriptInfo(child, circuit_list_vars)
                        if sub_info:
                            subscripts.append(sub_info)
                
                if subscripts:
                    loop_info.append({
                        'loop_vars': loop_vars,
                        'iter': iter_dump,
                        'subscripts': subscripts
                    })
        
        return loop_info

    def _compareSubscripts(self, buggy_subs, patched_subs):
        def group_by_value(subs):
            grouped = {}
            for sub in subs:
                val = sub['value']
                if val not in grouped:
                    grouped[val] = []
                grouped[val].append(sub)
            return grouped
        
        buggy_grouped = group_by_value(buggy_subs)
        patched_grouped = group_by_value(patched_subs)
        
        buggy_keys = set(buggy_grouped.keys())
        patched_keys = set(patched_grouped.keys())
        
        if buggy_keys != patched_keys:
            return True
        
        for key in buggy_keys:
            b_accesses = buggy_grouped[key]
            p_accesses = patched_grouped[key]
            
            for i in range(min(len(b_accesses), len(p_accesses))):
                b_acc = b_accesses[i]
                p_acc = p_accesses[i]
                
                if b_acc['index'] != p_acc['index']:
                    return True
                
                if b_acc['slice_type'] != p_acc['slice_type']:
                    return True
        
        return False

    def _checkAllSubscripts(self, code_ast, circuit_list_vars):
        index_access = []
        for node in code_ast:
            if isinstance(node, ast.Subscript):
                sub_info = self._extractSubscriptInfo(node, circuit_list_vars)
                if sub_info:
                    index_access.append({
                        'slice': node.slice,
                        'value': sub_info['value']
                    })
        return index_access

    def _checkIndexAccess(self, codeDiff, astSample, circuit_list_vars_buggy, circuit_list_vars_patched):

        buggy, patched = codeDiff[0], codeDiff[1]
        buggyList = list(filter(("").__ne__, buggy.split("\n")))
        patchedList = list(filter(("").__ne__, patched.split("\n")))

        buggyAST, patchedAST = ast.walk(astSample[0]), ast.walk(astSample[1])    

        buggy_index_access = self._checkAllSubscripts(buggyAST, circuit_list_vars_buggy)
        patched_index_access = self._checkAllSubscripts(patchedAST, circuit_list_vars_patched)

        if len(buggy_index_access) == 0 and len(patched_index_access) == 0:
            return False

        if len(buggy_index_access) != len(patched_index_access):
            return True
        
        buggy_by_value = {}
        for item in buggy_index_access:
            val = item['value']
            if val not in buggy_by_value:
                buggy_by_value[val] = []
            buggy_by_value[val].append(item['slice'])
        
        patched_by_value = {}
        for item in patched_index_access:
            val = item['value']
            if val not in patched_by_value:
                patched_by_value[val] = []
            patched_by_value[val].append(item['slice'])
        
        if set(buggy_by_value.keys()) != set(patched_by_value.keys()):
            return True
        
        for val in buggy_by_value:
            b_slices = buggy_by_value[val]
            p_slices = patched_by_value[val]
            
            if len(b_slices) != len(p_slices):
                return True
            
            for i in range(len(b_slices)):
                b_slice = b_slices[i]
                p_slice = p_slices[i]
                
                if b_slice is None or p_slice is None:
                    if b_slice != p_slice:
                        return True
                    continue
                
                if type(b_slice) != type(p_slice):
                    return True
                
                if isinstance(b_slice, ast.Slice):
                    if ast.dump(b_slice) != ast.dump(p_slice):
                        return True
                elif isinstance(b_slice, ast.Name):
                    if b_slice.id != p_slice.id:
                        return True
                elif isinstance(b_slice, ast.Constant):
                    if b_slice.value != p_slice.value:
                        return True
                elif isinstance(b_slice, ast.BinOp):
                    if ast.dump(b_slice) != ast.dump(p_slice):
                        return True
                elif hasattr(b_slice, '__dict__') and hasattr(p_slice, '__dict__'):
                    if b_slice.__dict__ != p_slice.__dict__:
                        return True
                else:
                    if ast.dump(b_slice) != ast.dump(p_slice):
                        return True

        return False

    def _checkRepresentation(self, codeDiff, astSample):

        buggy, patched = codeDiff[0], codeDiff[1]
        buggyList = list(filter(("").__ne__, buggy.split("\n")))
        patchedList = list(filter(("").__ne__, patched.split("\n")))

        circuit_list_vars_buggy = self._identifyCircuitListVariables(astSample[0])
        circuit_list_vars_patched = self._identifyCircuitListVariables(astSample[1])
        
        if len(circuit_list_vars_buggy) == 0 and len(circuit_list_vars_patched) == 0:
            return False

        buggyAST, patchedAST = ast.walk(astSample[0]), ast.walk(astSample[1])
        
        buggy_binrep, patched_binrep = self._checkBinRepCalls(buggyAST), self._checkBinRepCalls(patchedAST)

        if len(buggy_binrep) != len(patched_binrep):
            return True
        else:
            for iter_ in range(0, len(buggy_binrep)):
                if buggy_binrep[iter_] != patched_binrep[iter_]:
                    return True

        buggyAST, patchedAST = ast.walk(astSample[0]), ast.walk(astSample[1])
        
        buggy_loops = self._checkLoopIndexUsage(buggyAST, circuit_list_vars_buggy)
        patched_loops = self._checkLoopIndexUsage(patchedAST, circuit_list_vars_patched)
        
        if len(buggy_loops) != len(patched_loops):
            return True
        
        for i in range(min(len(buggy_loops), len(patched_loops))):
            b_loop = buggy_loops[i]
            p_loop = patched_loops[i]
            
            if b_loop['loop_vars'] != p_loop['loop_vars']:
                return True
            
            if b_loop['iter'] != p_loop['iter']:
                return True
            
            if self._compareSubscripts(b_loop['subscripts'], p_loop['subscripts']):
                return True

        if len(circuit_list_vars_buggy) > 0 or len(circuit_list_vars_patched) > 0:
            if self._checkIndexAccess(codeDiff, astSample, circuit_list_vars_buggy, circuit_list_vars_patched):
                return True

        return False

    def _detectIncorrectDecisionToMeasure(self, codeDiff, astSample):
        status = False
        bugTypeMessage = "Incorrect Decision To Measure detected."
        try:
            status = self._checkRepresentation(codeDiff, astSample)
        except:
            status = False
            print("error in checkRepresentation")
            raise

        return status, bugTypeMessage

    def assessBugType(self, codeSample, astSample):
        return self._detectIncorrectDecisionToMeasure(codeSample, astSample)