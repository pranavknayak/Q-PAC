# buggy version
grover_circuit = initialize_s(grover_circuit, [0, 1])
grover_circuit.ccx(0, 1, 0)  # Incorrect: Replacing CZ gate with Toffoli (CCX) gate in oracle"