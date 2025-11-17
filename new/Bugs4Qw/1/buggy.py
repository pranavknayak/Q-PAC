from qiskit import *
from qiskit.visualization import circuit_drawer
#definitions
c = ClassicalRegister(2)
q = QuantumRegister(1)
qc = QuantumCircuit(q,c)

# building the circuit
qc.h(q)
qc.measure(q[0],c[0])
qc.x(q[0]).c_if(c[0], 0)
qc.measure(q[0],c[1])
circuit_drawer(qc)
