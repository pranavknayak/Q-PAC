from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
qc = QuantumCircuit(3, 3)
qc.h(0)
qc.x(range(3))
qc.measure([0,1], [1, 0])