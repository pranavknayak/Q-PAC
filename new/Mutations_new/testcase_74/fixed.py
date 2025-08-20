qc = QuantumCircuit(4, 4)
gt1 = Gate('gt1', 2, [])
gt2 = Gate('gt2', 2, [])
# Intermediate logic to emulate gate behaviour by circuits
qc.append(gt1, [0, 1])
qc.append(gt2, [1, 2])