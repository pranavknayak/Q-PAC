from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
qreg = QuantumRegister(3)
creg = ClassicalRegister(2)
circuit = QuantumCircuit(qreg, creg)
circuit.y(0)
circuit.cx(0, 1)
circuit.cx(1, 2)
circuit.measure([0,1,2], [0,1,2])