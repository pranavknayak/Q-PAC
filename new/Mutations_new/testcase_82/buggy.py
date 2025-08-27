
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.circuit import Gate
import math

qr = QuantumRegister(5)
cr = ClassicalRegister(5)
qc = QuantumCircuit(qr, cr)

# Incorrect: Over-rotation resulting in non-unitary behavior
qc.rx(4 * math.pi, qr[4])  # Rotation angle exceeds the valid range