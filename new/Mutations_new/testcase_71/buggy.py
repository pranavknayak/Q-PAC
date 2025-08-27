from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.circuit import Gate
qc = QuantumCircuit(3, 3)
gt = Gate('gt', 3, []) 
qc.append(gt, [0, 1, 2])