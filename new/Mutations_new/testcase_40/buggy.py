# buggy version
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
q = QuantumRegister(2)
c = ClassicalRegister(2) 
grover_circuit = QuantumCircuit(q, c)
# grover_circuit = initialize_s(grover_circuit, [0, 1])
grover_circuit.z(0)  # Incorrect: Applying Z gate only to qubit 0 (qubit 1 is not targeted)