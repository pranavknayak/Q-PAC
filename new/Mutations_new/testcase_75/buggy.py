from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
a = QuantumCircuit(2)
a.sdg(1)
a.draw()