from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
# buggy version
q = QuantumRegister(2)
c = ClassicalRegister(2) 
grover_circuit = QuantumCircuit(q, c)
# grover_circuit = initialize_s(grover_circuit, [0, 1])
# grover_circuit.cz(0, 1)  # Incorrect: Removing the controlled-Z gate from the oracle"
grover_circuit.h([0,1])
grover_circuit.z([0,1])
grover_circuit.cz(0,1)
grover_circuit.h([0,1])