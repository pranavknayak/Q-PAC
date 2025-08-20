qc = QuantumCircuit(3, 3)
qc.h(0)
qc.x(range(3))
qc.measure([0,1], [0, 1])