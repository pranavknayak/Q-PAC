import ast
import re


class NumericalStability:
    def __init__(self):
        self.aggregationFunctions = [
            "max",
            "min",
            "sum",
            "mean",
            "median",
            "std",
            "prod",
            "cumsum",
            "all",
            "any",
        ]

    def _checkNumStabIncrease(self, codeSample, AstSample):
        astBuggy, astPatched = AstSample[0], AstSample[1]
        buggyArrs, patchedArrs = {}, {}
        buggyAggs, patchedAggs = {}, {}
        for node in ast.walk(astBuggy):
            if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
                varName = node.targets[0].id
                if isinstance(node.value, ast.Call):
                    if (
                        isinstance(node.value.func, ast.Attribute)
                        and isinstance(node.value.func.value, ast.Name)
                        and node.value.func.value.id in ["numpy", "np", "torch"]
                    ):
                        list_wrapper = node.value
                        if isinstance(list_wrapper.args[0], ast.List):
                            if node.value.func.attr in ["array", "tensor"]:
                                arr_list = list_wrapper.args[0]
                                arr_len = len(arr_list.elts)
                                buggyArrs[varName] = [
                                    arr_len,
                                ]
                            elif node.value.func.attr in self.aggregationFunctions:
                                arr_list = list_wrapper.args[0]
                                arr_len = len(arr_list.elts)
                                entry = [arr_len, node.value.func.attr]
                                if varName in buggyAggs:
                                    buggyAggs[varName].append(('inline', entry))
                                else:
                                    buggyAggs[varName] = [('inline', entry)]

                        elif (
                            isinstance(list_wrapper.args[0], ast.Name)
                            and list_wrapper.args[0].id in buggyArrs.keys()
                            and isinstance(list_wrapper.func, ast.Attribute)
                            and list_wrapper.func.attr in self.aggregationFunctions
                        ):
                            buggyArrs[list_wrapper.args[0].id].append(
                                list_wrapper.func.attr
                            )
                            if isinstance(node.targets[0], ast.Name):
                                if node.targets[0].id in buggyAggs:
                                    buggyAggs[node.targets[0].id].append(
                                        (
                                            list_wrapper.args[0].id,
                                            buggyArrs[list_wrapper.args[0].id],
                                        )
                                    )
                                else:
                                    buggyAggs[node.targets[0].id] = [
                                        (
                                            list_wrapper.args[0].id,
                                            buggyArrs[list_wrapper.args[0].id],
                                        ),
                                    ]
                    elif (
                        isinstance(node.value.func, ast.Name)
                        and isinstance(node.value.args[0], ast.Name)
                        and node.value.args[0].id in buggyArrs
                        and node.value.func.id in self.aggregationFunctions
                    ):
                        buggyArrs[node.value.args[0].id].append(node.value.func.id)
                        if isinstance(node.targets[0], ast.Name):
                            if node.targets[0].id in buggyAggs:
                                buggyAggs[node.targets[0].id].append(
                                    (
                                        node.value.args[0].id,
                                        buggyArrs[node.value.args[0].id],
                                    )
                                )
                            else:
                                buggyAggs[node.targets[0].id] = [
                                    (
                                        node.value.args[0].id,
                                        buggyArrs[node.value.args[0].id],
                                    ),
                                ]

                    elif (
                        isinstance(node.value.func, ast.Name)
                        and isinstance(node.value.args[0], ast.List)
                        and node.value.func.id in self.aggregationFunctions
                    ):
                        arr_list = node.value.args[0]
                        arr_len = len(arr_list.elts)
                        entry = [arr_len, node.value.func.id]
                        if isinstance(node.targets[0], ast.Name):
                            if node.targets[0].id in buggyAggs:
                                buggyAggs[node.targets[0].id].append(('inline', entry))
                            else:
                                buggyAggs[node.targets[0].id] = [('inline', entry)]

                elif isinstance(node.value, ast.List):
                    arr_list = node.value
                    arr_len = len(arr_list.elts)
                    buggyArrs[varName] = [
                        arr_len,
                    ]

        for node in ast.walk(astPatched):
            if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
                varName = node.targets[0].id
                if isinstance(node.value, ast.Call):
                    if (
                        isinstance(node.value.func, ast.Attribute)
                        and isinstance(node.value.func.value, ast.Name)
                        and node.value.func.value.id in ["numpy", "np", "torch"]
                    ):
                        list_wrapper = node.value
                        if isinstance(list_wrapper.args[0], ast.List):
                            if node.value.func.attr in ["array", "ndarray", "tensor"]:
                                arr_list = list_wrapper.args[0]
                                arr_len = len(arr_list.elts)
                                patchedArrs[varName] = [
                                    arr_len,
                                ]
                            elif node.value.func.attr in self.aggregationFunctions:
                                arr_list = list_wrapper.args[0]
                                arr_len = len(arr_list.elts)
                                entry = [arr_len, node.value.func.attr]
                                if varName in patchedAggs:
                                    patchedAggs[varName].append(('inline', entry))
                                else:
                                    patchedAggs[varName] = [('inline', entry)]

                        elif (
                            isinstance(list_wrapper.args[0], ast.Name)
                            and list_wrapper.args[0].id in patchedArrs.keys()
                            and isinstance(list_wrapper.func, ast.Attribute)
                            and list_wrapper.func.attr in self.aggregationFunctions
                        ):
                            patchedArrs[list_wrapper.args[0].id].append(
                                list_wrapper.func.attr
                            )
                            if isinstance(node.targets[0], ast.Name):
                                if node.targets[0].id in patchedAggs:
                                    patchedAggs[node.targets[0].id].append(
                                        (
                                            list_wrapper.args[0].id,
                                            patchedArrs[list_wrapper.args[0].id],
                                        )
                                    )
                                else:
                                    patchedAggs[node.targets[0].id] = [
                                        (
                                            list_wrapper.args[0].id,
                                            patchedArrs[list_wrapper.args[0].id],
                                        ),
                                    ]
                    elif (
                        isinstance(node.value.func, ast.Name)
                        and isinstance(node.value.args[0], ast.Name)
                        and node.value.args[0].id in patchedArrs
                        and node.value.func.id in self.aggregationFunctions
                    ):
                        patchedArrs[node.value.args[0].id].append(node.value.func.id)
                        if isinstance(node.targets[0], ast.Name):
                            if node.targets[0].id in patchedAggs:
                                patchedAggs[node.targets[0].id].append(
                                    (
                                        node.value.args[0].id,
                                        patchedArrs[node.value.args[0].id],
                                    )
                                )
                            else:
                                patchedAggs[node.targets[0].id] = [
                                    (
                                        node.value.args[0].id,
                                        patchedArrs[node.value.args[0].id],
                                    ),
                                ]

                    elif (
                        isinstance(node.value.func, ast.Name)
                        and isinstance(node.value.args[0], ast.List)
                        and node.value.func.id in self.aggregationFunctions
                    ):
                        arr_list = node.value.args[0]
                        arr_len = len(arr_list.elts)
                        entry = [arr_len, node.value.func.id]
                        if isinstance(node.targets[0], ast.Name):
                            if node.targets[0].id in patchedAggs:
                                patchedAggs[node.targets[0].id].append(('inline', entry))
                            else:
                                patchedAggs[node.targets[0].id] = [('inline', entry)]

                elif isinstance(node.value, ast.List):
                    arr_list = node.value
                    arr_len = len(arr_list.elts)
                    patchedArrs[varName] = [
                        arr_len,
                    ]

        for stat in patchedAggs.keys():
            if stat in buggyAggs.keys():
                buggyLength = buggyAggs[stat][-1][1][0]
                patchedLength = patchedAggs[stat][-1][1][0]
                if buggyLength < patchedLength:
                    return True, 'Numeraical Stability Check Failed'
            else:
                continue
        
        return False, 'None'

    def assessBugType(self, codeSample, astSample):
        return self._checkNumStabIncrease(codeSample, astSample)


# Write code for entry when called by QPAC
if __name__ == "__main__":

    codeSample1 = """
a = [1, 2, 3]
b = np.array([5, 6, 7, 8])
a1 = np.max(a)
b1 = min(b)
    """
    codeSample2 = """
a = [1, 2]
b = np.array([5, 6])
a1 = np.max(a)
b1 = min(b)
    """

    tree = (ast.walk(ast.parse(codeSample1)), ast.walk(ast.parse(codeSample2)))

    detector = NumericalStability()
    output = detector._checkNumStabIncrease((codeSample1, codeSample2), tree)
    print(output)
