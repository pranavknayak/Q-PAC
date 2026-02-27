from qiskit.circuit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.quantum_info import Operator

qr = QuantumRegister(5)
cr = ClassicalRegister(5)
qc = QuantumCircuit(qr, cr)

inner = QuantumCircuit(1, name="inner")
# Fix: Use a valid unitary matrix in nested circuit
inner.unitary(Operator([[1, 0], [0, 1.0]]), [0])
inner.unitary(Operator([[1, 0], [0, 1.21]]), [1])

outer = QuantumCircuit(1, name="outer")
outer.append(inner.to_gate(), [0])

qc.append(outer.to_gate(), [qr[4]])