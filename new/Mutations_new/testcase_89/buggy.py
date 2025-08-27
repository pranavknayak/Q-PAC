from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
circ = QuantumCircuit(3, 3)
circ.y(0)
circ.cx(0, 1)
circ.cx(1, 2)
circ.measure([0,1,2], [0,1,2])
