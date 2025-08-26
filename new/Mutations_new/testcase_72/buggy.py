from qiskit import QuantumCircuit
from qiskit.circuit import Gate
qc = QuantumCircuit(3, 3)
gt = Gate('gt', 2, [])
qc.append(gt, [0, 1])
subc = QuantumCircuit(2, name='subc')
subc.h(0)
subc.cx(0, 1)
subc.h(0)
gt2 = subc.to_instruction()
qc.append(gt2, [1, 2])