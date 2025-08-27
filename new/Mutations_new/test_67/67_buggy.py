from qiskit import QuantumCircuit
def measure(circuit):
    return circuit.measure(0)

circ1 = Quantumcircuit(3)
circ2 = Quantumcircuit(3)
circ3 = Quantumcircuit(3)
circ4 = Quantumcircuit(3)
circ5 = Quantumcircuit(3)

out1 = measure(circ1)
out2 = measure(circ2)
out3 = measure(circ3)
out4 = measure(circ4)
out5 = measure(circ5)
total_output = sum([out1, out2])  # Buggy
