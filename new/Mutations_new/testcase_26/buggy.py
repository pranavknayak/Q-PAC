# buggy version
grover_circuit = initialize_s(grover_circuit, [0, 1])
grover_circuit.cy(0, 1)  # Incorrect: Replacing CZ gate with CY gate in oracle"