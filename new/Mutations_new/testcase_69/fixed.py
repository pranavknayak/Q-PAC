q = QuantumCircuit(3, 3)
q.h(0)
q.x(range(3))
q.measure([0,1], [0, 1])