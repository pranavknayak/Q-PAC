# buggy version
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
q = QuantumRegister(2)
c = ClassicalRegister(1)  # Classical register with only 1 bit
grover_circuit = QuantumCircuit(q, c)
# grover_circuit = initialize_s(grover_circuit, [0, 1])
grover_circuit.cz(q[0], q[1])
grover_circuit.h([0, 1])
grover_circuit.z([0, 1])
grover_circuit.cz(q[0], q[1])
grover_circuit.h([0, 1])
grover_circuit.measure(q, [0])  # Attempting to measure both qubits into a single classical bit"