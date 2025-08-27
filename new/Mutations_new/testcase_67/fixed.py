from qiskit import QuantumCircuit
qc = QuantumCircuit(3, 3)
qc.h(0)
qc.measure([0,1], [0, 1])
qc.x(range(3))