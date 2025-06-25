# buggy version
grover_circuit.h([0, 1])  # Correct: Apply Hadamard gates for initialization
grover_circuit.h([0, 1])  # Start diffusion operator
grover_circuit.cz(q[0], q[1])  # Incorrect: Applying CZ gate (oracle) in the middle of diffusion
grover_circuit.z([0, 1])  # Z gate in diffusion
grover_circuit.h([0, 1])