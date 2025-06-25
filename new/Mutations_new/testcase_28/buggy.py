# buggy version
grover_circuit = initialize_s(grover_circuit, [0, 1])
grover_circuit.cz(0, 1)  # Oracle
grover_circuit.h([0, 1])
# grover_circuit.z([0, 1])  # Incorrect: Removing the Z gate in the diffusion operator
grover_circuit.cz(0, 1)
grover_circuit.h([0, 1])