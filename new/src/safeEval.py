import importlib

def safeEval(expr, context):
    try:
        return eval(expr, context)
    except NameError as e:
        missing_name = str(e).split("'")[1]
        # Example mapping of known quantum libraries
        known_sources = {
            'QuantumCircuit': 'qiskit',
            'QuantumRegister': 'qiskit',
            'ClassicalRegister': 'qiskit',
        }
        if missing_name in known_sources:
            module = importlib.import_module(known_sources[missing_name])
            context[missing_name] = getattr(module, missing_name)
            return safeEval(expr, context)
        else:
            raise