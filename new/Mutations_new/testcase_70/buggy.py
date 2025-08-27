from qiskit import QuantumCircuit
qc = QuantumCircuit(2, 2)
qc.x(0)
qc.h(0)
qc.measure(0, 0)