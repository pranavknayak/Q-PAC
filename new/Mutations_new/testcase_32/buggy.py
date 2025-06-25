# buggy version
grover_circuit.h([0, 1])  # Correct Hadamard gates for initialization
grover_circuit.x(0)  # Incorrect: Adding an extra X gate before the oracle for qubit 0
grover_circuit.cz(0, 1)  # Oracle
grover_circuit.h([0, 1])  # Diffusion operator
grover_circuit.z([0, 1])
grover_circuit.cz(0, 1)
grover_circuit.h([0, 1])
grover_circuit.measure_all()