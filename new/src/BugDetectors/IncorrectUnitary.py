import numpy as np
import ast
import builtins
import re
#import qiskit.exceptions
from qiskit.exceptions import QiskitError
from qiskit_aer.noise.noiseerror import NoiseError
from safeExec import safeExec

class IncorrectUnitary():

    def _isUnitary(self, matrix, tol=1e-10):
        """
        Check if a matrix is unitary.

        Parameters:
        matrix (numpy.ndarray): The matrix to check.
        tol (float): Tolerance for numerical errors.

        Returns:
        bool: True if the matrix is unitary, False otherwise.
        """
        if matrix.shape[0] != matrix.shape[1]:
            return False
        identity = np.eye(matrix.shape[0])
        unitaryCheck = np.allclose(matrix.conj().T @ matrix, identity, atol=tol)
        return unitaryCheck

    def _extractArraysFromCode(self, code):
        """
        Execute code in a controlled environment and extract arrays.

        Parameters:
        code (str): The code string to execute.

        Returns:
        dict: A dictionary mapping variable names to numpy arrays.
        """
        arrays = {}
        variables = {}
        # Controlled execution environment
        #safeGlobals = {'__builtins__': None, 'np': np}
        safeGlobals = {
            '__builtins__': {
                '__import__': builtins.__import__,
                'abs':     builtins.abs,      # if you need abs()
                # ...any other built-ins you explicitly want to allow
            },
            'np': np
        }

        tree = ast.parse(code, mode='exec')        
        compiled = compile(tree, filename="<sandbox>", mode="exec")
        # status = exec(code, safeGlobals, variables)
        status = safeExec(code, safeGlobals, variables)
        # Recursively extract arrays from variables
        for varName, value in variables.items():
            foundArrays = self._extractArraysFromObject(value, varName)
            arrays.update(foundArrays)

        return arrays

    def _extractArraysFromObject(self, obj, name):
        """
        Recursively extract arrays from an object (dicts, lists, numpy arrays).

        Parameters:
        obj: The object to search.
        name: The name of the variable or key.

        Returns:
        dict: A dictionary mapping variable names to numpy arrays.
        """
        arrays = {}
        if isinstance(obj, np.ndarray):
            arrays[name] = obj
        elif isinstance(obj, dict):
            for key, value in obj.items():
                keyName = f"{name}['{key}']"
                arrays.update(self._extractArraysFromObject(value, keyName))
        elif isinstance(obj, list):
            for idx, item in enumerate(obj):
                idxName = f"{name}[{idx}]"
                arrays.update(self._extractArraysFromObject(item, idxName))
        return arrays

    def _identifyNonUnitaryArrays(self, correctCode, buggyCode):
        """
        Identify arrays that are unitary in the correct code but not unitary in the buggy code.

        Parameters:
        correctCode (str): The correct Python code.
        buggyCode (str): The buggy Python code.

        Returns:
        list: A list of variable names that lead to non-unitary matrices.
        """
        correctArrays = self._extractArraysFromCode(correctCode)
        buggyArrays = self._extractArraysFromCode(buggyCode)
        nonUnitaryArrays = []
        for varName, correctArr in correctArrays.items():
            if isinstance(correctArr, np.ndarray):
                # Check if the array is unitary in the correct code
                if self._isUnitary(correctArr):
                    # Check if the corresponding array exists in the buggy code
                    if varName in buggyArrays:
                        buggyArr = buggyArrays[varName]
                        if isinstance(buggyArr, np.ndarray):
                            # Check if the buggy array is not unitary
                            if not self._isUnitary(buggyArr):
                                nonUnitaryArrays.append(varName)
        return nonUnitaryArrays

    def _snippet_raises_amplitude_or_CPTP_error(self, code: str) -> bool:
        """
        Execute the given code snippet and return True if it raises exactly
        the QiskitError:

            "Sum of amplitudes-squared is not 1, but {norm}."

        and False for any other outcome (successful run or different error).
        """
        # Prepare isolated namespaces
        globals_dict = {}
        locals_dict = {}

        try:
            # exec(code, globals_dict, locals_dict)
            exec(code, globals_dict, locals_dict)
            return False
        except (QiskitError, NoiseError) as e:
            # Check that the message matches the amplitude‐norm error
            msg = str(e)
            print(msg)
            if msg.startswith("'Sum of amplitudes-squared is not 1,") or 'not CPTP' in msg:
                return True
            return False
        except (IndexError, AttributeError, ValueError, TypeError, KeyError, NameError):
            # Runtime errors in buggy code (invalid qubit indices, missing gates, undefined vars, etc.) -> not a unitary error
            return False

    def _extract_operator_matrices_from_source(self, code):
        """
        Extract matrix literals from Operator(...) calls in source code.
        Handles matrices of any size (2x2, 4x4, 8x8, etc.).
        Returns list of numpy arrays.
        """
        matrices = []
        
        # Pattern to match Operator([...]) with any number of rows
        # Captures the entire matrix content between Operator( and )
        pattern = r'Operator\s*\(\s*\[\s*((?:\[.*?\]\s*,?\s*)+)\s*\]\s*\)'
        
        matches = re.findall(pattern, code, re.DOTALL)
        
        for match in matches:
            try:
                # Extract all rows: find all [...] patterns
                rows_pattern = r'\[(.*?)\]'
                rows = re.findall(rows_pattern, match)
                
                if len(rows) < 2:  # Need at least 2 rows for a valid matrix
                    continue
                
                # Extract numbers from each row
                matrix_rows = []
                for row_str in rows:
                    row_nums = re.findall(r'-?\d+\.?\d*(?:[eE][+-]?\d+)?', row_str)
                    if row_nums:
                        matrix_rows.append([float(x) for x in row_nums])
                
                if len(matrix_rows) >= 2:
                    # Verify all rows have same length (square matrix)
                    row_length = len(matrix_rows[0])
                    if all(len(row) == row_length for row in matrix_rows):
                        matrix = np.array(matrix_rows, dtype=complex)
                        matrices.append(matrix)
            except (ValueError, IndexError):
                continue
        
        return matrices

    def _detectIncorrectUnitary(self, codeDiff, astSample):
        bugTypeMessage = "Non-unitary matrix(ces) (which is/are supposed to be unitary) found."
        status = False
        
        buggy_code = codeDiff[0]
        patched_code = codeDiff[1]
        
        # Try error-based detection first
        if (not self._snippet_raises_amplitude_or_CPTP_error(patched_code)) and self._snippet_raises_amplitude_or_CPTP_error(buggy_code):
            status = True
        
        # If no error-based detection, try source code analysis
        if status is False:
            # Extract matrices from source code
            buggy_matrices = self._extract_operator_matrices_from_source(buggy_code)
            patched_matrices = self._extract_operator_matrices_from_source(patched_code)
            
            # Check if we have matrices to compare
            if buggy_matrices and patched_matrices:
                # Find non-unitary matrices in buggy that are fixed in patched
                for i, buggy_mat in enumerate(buggy_matrices):
                    if i < len(patched_matrices):
                        patched_mat = patched_matrices[i]
                        buggy_is_unitary = self._isUnitary(buggy_mat)
                        patched_is_unitary = self._isUnitary(patched_mat)
                        
                        # If buggy is non-unitary but patched is unitary, we found the bug
                        if not buggy_is_unitary and patched_is_unitary:
                            print(f"\nUNITARY ERROR: Found non-unitary matrix at position {i}")
                            print(f"  Buggy matrix:\n{buggy_mat}")
                            print(f"  Patched matrix:\n{patched_mat}")
                            status = True
                            break
            
            # Try array extraction method as backup
            if status is False:
                non_unitary_gate_array = self._identifyNonUnitaryArrays(patched_code, buggy_code)
                if non_unitary_gate_array != []:
                    print(f"\nUNITARY ERROR: Non-unitary matrices found in {', '.join(non_unitary_gate_array)}")
                    status = True
            
            if status is False:
                bugTypeMessage = None
        
        return status, bugTypeMessage
    
    def assessBugType(self, codeSample, astSample):
        return self._detectIncorrectUnitary(codeSample, astSample)
