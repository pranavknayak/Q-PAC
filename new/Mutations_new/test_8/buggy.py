from qiskit import QuantumCircuit
from qiskit.primitives import Sampler

circuits = [QuantumCircuit(1) for _ in range(3)]
for qc in circuits:
    qc.h(0)
    qc.measure_all()

sampler = Sampler()
result = sampler.run(circuits).result()

for qc in circuits:
    data = result.quasi_dists[qc]  # WRONG: using circuit object as index
    print(data)