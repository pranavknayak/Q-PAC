from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.circuit import Gate

qr = QuantumRegister(5)
cr = ClassicalRegister(5)
qc = QuantumCircuit(qr, cr)

# Correct: Use transpilation to optimize gates and maintain unitarity
qc = transpile(qc, optimization_level=3)