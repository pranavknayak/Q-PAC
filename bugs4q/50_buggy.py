q = QuantumRegister(2,'q')
c = ClassicalRegister(2,'c')
qc = QuantumCircuit(q,c)
qc.h(q[0])
qc.cx(q[0], q[1])
qc.measure(q[0],c[0])
qc.measure(q[1],c[1])

dag = circuit_to_dag(qc)
coupling = CouplingMap(backend.configuration().coupling_map)
pm = PassManager()
pm.append(DenseLayout(coupling))
pm.append(StochasticSwap(coupling))
pm.append(Decompose(SwapGate))
new_dag = pm.run_passes(dag)
