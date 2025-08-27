from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister

qr = QuantumRegister(5)
cr = ClassicalRegister(5)
qc = QuantumCircuit(qr, cr)

# Incorrect: Non-normalized state vector
initial_state = [1, 1]  # Not normalized
qc.initialize(initial_state, qr[0])