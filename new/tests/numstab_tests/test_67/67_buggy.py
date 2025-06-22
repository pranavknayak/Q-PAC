def measure(circuit):
    return circuit.measure(0)

out1 = measure(circ1)
out2 = measure(circ2)
total_output = sum([out1, out2])  # Buggy
