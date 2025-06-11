import numpy as np
import ast
import builtins

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

        # try:
            
        # except Exception as e:
        #     print(f"Error executing code: {e}")

        print(code, safeGlobals, variables, sep="*********\n")
        tree = ast.parse(code, mode='exec')        
        compiled = compile(tree, filename="<sandbox>", mode="exec")
        status = exec(code, safeGlobals, variables)
        print("status:", status)
        print("variables:", variables)
        print("safeGlobals:", safeGlobals)
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

def snippet_raises_amplitude_error(code: str) -> bool:
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
        exec(code, globals_dict, locals_dict)
        return False
    except QiskitError as e:
        # Check that the message matches the amplitude‐norm error
        msg = str(e)
        if msg.startswith("Sum of amplitudes-squared is not 1, but"):
            return True
        return False
    except Exception:
        # Any other exception (or successful execution) → False
        return False

    def _detectIncorrectUnitary(self, codeDiff, astSample):
        bugTypeMessage = None
        status = self._identifyNonUnitaryArrays(codeDiff[1], codeDiff[0])
        if (status is not None) or ((not snippet_raises_amplitude_error(codeDiff[1])) and snippet_raises_amplitude_error(codeDiff[0])) :
            status = True
            bugTypeMessage = "Non-unitary matrix(ces) (which is/are supposed to be unitary) found."
        else:
            status = False
            
        
        return status, bugTypeMessage
    
    def assessBugType(self, codeSample, astSample):
        return self._detectIncorrectUnitary(codeSample, astSample)
