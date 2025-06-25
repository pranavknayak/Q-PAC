# buggy version
grover_circuit.h([0, 1])  # Correct Hadamard gates for initialization
grover_circuit.cz(0, 1)  # Oracle
grover_circuit.h([0, 1])
grover_circuit.cx(0, 1)  # Incorrect: Adding extra CX gate in the diffusion operator
grover_circuit.z([0, 1])
grover_circuit.cz(0, 1)
grover_circuit.h([0, 1])
grover_circuit.measure_all()