# buggy version
grover_circuit = initialize_s(grover_circuit, [0,1])
grover_circuit.cz(0,1)  # Oracle
grover_circuit.h([0,1])
grover_circuit.z([0,1])
grover_circuit.cz(0,1)
grover_circuit.h([0,1])
grover_circuit.measure(1, 0)  # Only measuring qubit 1 into classical bit 0"