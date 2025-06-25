# buggy version
grover_circuit.h([0, 1])  # Correct: Apply Hadamard gates for initialization
grover_circuit.h([0, 1])  # Diffusion operator
grover_circuit.z([0, 1])
grover_circuit.cz(q[0], q[1])
grover_circuit.h([0, 1])
grover_circuit.cz(q[0], q[1])  # Incorrect: Oracle applied after diffusion operator"