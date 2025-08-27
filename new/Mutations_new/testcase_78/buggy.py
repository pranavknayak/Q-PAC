from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
qc = QuantumCircuit(3, 3)
qc.h(0)
qc.x([0,1,2])
qc.measure([0,1], [0, 1])