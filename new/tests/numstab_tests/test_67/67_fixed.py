def measure(circuit):
    return circuit.measure(0)

out3 = measure(circ3)
out4 = measure(circ4)
out5 = measure(circ5)
total_output = sum([out1, out2, out3, out4, out5]) 
