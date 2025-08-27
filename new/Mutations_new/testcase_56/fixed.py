from qiskit import QuantumCircuit
qc = QuantumCircuit(2)
qc.h(1)
qc.cx(0,1)