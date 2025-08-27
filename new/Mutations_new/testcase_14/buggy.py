from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
# buggy version
q = QuantumRegister(2)
c = ClassicalRegister(2) 
grover_circuit = QuantumCircuit(q, c)
# grover_circuit = initialize_s(grover_circuit, [0, 1])
grover_circuit.measure_all()  # Measure after initialization (Hadamard gates)
grover_circuit.cz(q[0], q[1])  # Oracle
grover_circuit.measure_all()  # Measure after oracle
grover_circuit.h([0, 1])  # Diffusion operator step 1
grover_circuit.measure_all()  # Measure after Hadamard gates in diffusion operator
grover_circuit.z([0, 1])  # Diffusion operator step 2
grover_circuit.measure_all()  # Measure after Pauli-Z gates
grover_circuit.cz(q[0], q[1])  # Controlled-Z gate in diffusion
grover_circuit.measure_all()  # Measure after controlled-Z
grover_circuit.h([0, 1])  # Final Hadamard gates
grover_circuit.measure_all()  # Final measurement after all operations"