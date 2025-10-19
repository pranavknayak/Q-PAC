from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
qreg = QuantumRegister(3)
creg = ClassicalRegister(3)
circ = QuantumCircuit(qreg, creg)
circ.y(0)
circ.x(0)
circ.x(0)
circ.measure([0,1,2], [0,1,2])