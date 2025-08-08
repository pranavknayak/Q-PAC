# buggy version
q = QuantumRegister(2)
c = ClassicalRegister(2) 
grover_circuit = QuantumCircuit(q, c)
grover_circuit = initialize_s(grover_circuit, [0, 1])
grover_circuit.cz(q[0], q[1])
grover_circuit.h([0, 1])
grover_circuit.z([0, 1])
grover_circuit.cz(q[0], q[1])
grover_circuit.h([0, 1])
grover_circuit.measure([1, 0], [0, 1])  # Incorrect mapping: reverse order of qubits