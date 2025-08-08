# buggy version
q = QuantumRegister(2)
c = ClassicalRegister(2) 
grover_circuit = QuantumCircuit(q, c)
grover_circuit = initialize_s(grover_circuit, [0, 1])
grover_circuit.h([0, 1])  # Correct Hadamard gates for initialization
grover_circuit.cz(0, 1)  # Oracle
grover_circuit.swap(0, 1)  # Incorrect: Adding an extra SWAP gate after the oracle
grover_circuit.h([0, 1])  # Diffusion operator
grover_circuit.z([0, 1])
grover_circuit.cz(0, 1)
grover_circuit.h([0, 1])
grover_circuit.measure_all()