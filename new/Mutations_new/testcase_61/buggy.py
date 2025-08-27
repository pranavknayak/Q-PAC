from qiskit import QuantumCircuit
qc = QuantumCircuit(3)
qc.h(0)
qc.x(0 + 1)
qc.draw()