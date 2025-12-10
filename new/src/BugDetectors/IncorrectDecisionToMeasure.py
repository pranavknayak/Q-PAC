import ast 
import re


class IncorrectDecisionToMeasure():
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

    def _extractSubscriptInfo(self, node):
        """Extract detailed info about a subscript for comparison"""
        if not isinstance(node, ast.Subscript):
            return None
        
        # get what's being subscripted
        value_repr = ast.dump(node.value)
        
        # get the index/slice being used
        if isinstance(node.slice, ast.Name):
            index_repr = node.slice.id
            slice_type = 'name'
        elif isinstance(node.slice, ast.Constant):
            index_repr = str(node.slice.value)
            slice_type = 'constant'
        elif isinstance(node.slice, ast.Slice):
            # handle slicing like [1:] or [:5]
            index_repr = ast.dump(node.slice)
            slice_type = 'slice'
        elif isinstance(node.slice, ast.Index):  # older Python versions
            if isinstance(node.slice.value, ast.Name):
                index_repr = node.slice.value.id
                slice_type = 'name'
            elif isinstance(node.slice.value, ast.Constant):
                index_repr = str(node.slice.value.value)
                slice_type = 'constant'
            else:
                index_repr = ast.dump(node.slice.value)
                slice_type = 'other'
        else:
            index_repr = ast.dump(node.slice)
            slice_type = 'other'
        
        return {'value': value_repr, 'index': index_repr, 'slice_type': slice_type}

    def _checkLoopIndexUsage(self, code_ast):
        # track loop variables and subscript usage within loops
        loop_info = []
        
        for node in code_ast:
            if isinstance(node, ast.For):
                # get the loop variable(s)
                loop_vars = []
                if isinstance(node.target, ast.Name):
                    loop_vars.append(node.target.id)
                elif isinstance(node.target, ast.Tuple):
                    for n in node.target.elts:
                        if isinstance(n, ast.Name):
                            loop_vars.append(n.id)
                
                # get what's being iterated - need full dump to catch slicing
                iter_dump = ast.dump(node.iter)
                
                # collect all subscripts in loop body with their details
                subscripts = []
                for child in ast.walk(node):
                    if isinstance(child, ast.Subscript):
                        sub_info = self._extractSubscriptInfo(child)
                        if sub_info:
                            subscripts.append(sub_info)
                
                loop_info.append({
                    'loop_vars': loop_vars,
                    'iter': iter_dump,
                    'subscripts': subscripts
                })
        
        return loop_info

    def _compareSubscripts(self, buggy_subs, patched_subs):
        """Compare subscripts more intelligently by grouping by what's being accessed"""
        # group by the object being subscripted
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
        
        # check if same objects are being subscripted
        buggy_keys = set(buggy_grouped.keys())
        patched_keys = set(patched_grouped.keys())
        
        # if different objects accessed, that's a difference
        if buggy_keys != patched_keys:
            return True
        
        # for each object, compare how it's being accessed
        for key in buggy_keys:
            b_accesses = buggy_grouped[key]
            p_accesses = patched_grouped[key]
            
            # compare each access
            for i in range(min(len(b_accesses), len(p_accesses))):
                b_acc = b_accesses[i]
                p_acc = p_accesses[i]
                
                # if index changed
                if b_acc['index'] != p_acc['index']:
                    return True
                
                # if slice type changed (constant to variable, etc)
                if b_acc['slice_type'] != p_acc['slice_type']:
                    return True
        
        return False

    def _checkAllSubscripts(self, code_ast):
        index_access = []
        for node in code_ast:
            if isinstance(node, ast.Subscript):
                index_access.append(node.slice)
        print(index_access)
        return index_access

    def _checkIndexAccess(self, codeDiff, astSample):

        buggy, patched = codeDiff[0], codeDiff[1]
        buggyList = list(filter(("").__ne__, buggy.split("\n")))
        patchedList = list(filter(("").__ne__, patched.split("\n")))

        buggyAST, patchedAST = ast.walk(astSample[0]), ast.walk(astSample[1])    

        buggy_index_access, patched_index_access = self._checkAllSubscripts(buggyAST), self._checkAllSubscripts(patchedAST)

        if len(buggy_index_access) != len(patched_index_access):
            return True
        else:
            for iter_ in range(0, len(buggy_index_access)):
                print(buggy_index_access[iter_].__dict__, patched_index_access[iter_].__dict__)
                if type(buggy_index_access[iter_]) != type(patched_index_access[iter_]):
                    return True
                elif buggy_index_access[iter_].__dict__ != patched_index_access[iter_].__dict__:
                    return True
        return False

    def _hasLoopOrSubscript(self, code_ast):
        has_loop = False
        has_subscript = False
        for node in code_ast:
            if isinstance(node, ast.For):
                has_loop = True
            if isinstance(node, ast.Subscript):
                has_subscript = True
            if has_loop and has_subscript:
                break
        return has_loop, has_subscript

    def _checkRepresentation(self, codeDiff, astSample):

        buggy, patched = codeDiff[0], codeDiff[1]
        buggyList = list(filter(("").__ne__, buggy.split("\n")))
        patchedList = list(filter(("").__ne__, patched.split("\n")))

        buggyAST, patchedAST = ast.walk(astSample[0]), ast.walk(astSample[1])    

        buggy_binrep, patched_binrep = self._checkBinRepCalls(buggyAST), self._checkBinRepCalls(patchedAST)

        if len(buggy_binrep) != len(patched_binrep):
            return True
        else:
            for iter_ in range(0, len(buggy_binrep)):
                if buggy_binrep[iter_] != patched_binrep[iter_]:
                    return True

        buggyAST, patchedAST = ast.walk(astSample[0]), ast.walk(astSample[1])
        buggy_has_loop, buggy_has_sub = self._hasLoopOrSubscript(buggyAST)
        patched_has_loop, patched_has_sub = self._hasLoopOrSubscript(patchedAST)

        if not (buggy_has_loop or buggy_has_sub or patched_has_loop or patched_has_sub):
            return False

        buggyAST, patchedAST = ast.walk(astSample[0]), ast.walk(astSample[1])
        buggy_loops = self._checkLoopIndexUsage(buggyAST)
        patched_loops = self._checkLoopIndexUsage(patchedAST)
        
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

        if buggy_has_sub or patched_has_sub:
            if self._checkIndexAccess(codeDiff, astSample):
                return True

        return False

    def _detectIncorrectDecisionToMeasure(self, codeDiff, astSample):
        status = False
        bugTypeMessage = "Incorrect Decision To Measure detected."
        try:
            status = self._checkRepresentation(codeDiff, astSample)
            print("checkRepresentation WORKS")
        except:
            status = False
            print("error in checkRepresentation")
            raise

        return status, bugTypeMessage

    def assessBugType(self, codeSample, astSample):
        return self._detectIncorrectDecisionToMeasure(codeSample, astSample)