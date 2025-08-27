from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
import numpy as np

qr = QuantumRegister(5)
cr = ClassicalRegister(5)
qc = QuantumCircuit(qr, cr)

# Correct: Normalize the state vector
norm = np.linalg.norm([1, 1])
initial_state = [1 / norm, 1 / norm]
qc.initialize(initial_state, qr[0])