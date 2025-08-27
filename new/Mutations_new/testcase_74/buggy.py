from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.circuit import Gate
qc = QuantumCircuit(4, 4)
gt1 = Gate('gt', 3, []) 
gt2 = Gate('gt2', 3, [])
qc.append(gt1, [0, 1, 2])
qc.append(gt2, [1, 2, 3])