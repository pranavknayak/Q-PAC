# buggy version
grover_circuit.z(0)  # Correct: Applying Z gate to qubit 0
grover_circuit.z(0)  # Incorrect: Applying Z gate to qubit 0 again, instead of qubit 1
