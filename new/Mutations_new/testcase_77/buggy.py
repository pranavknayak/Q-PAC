from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
qc = QuantumCircuit(2,2)
qc.tdg(1)
qc.draw()