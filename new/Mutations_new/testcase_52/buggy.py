qc = QuantumCircuit(2, 2)
for i in range(5):
  qc.measure(0, 0)
qc.measure(0, 0)