from qiskit import QuantumCircuit
from qiskit.primitives import Sampler

circuits = [QuantumCircuit(1) for _ in range(4)]
for qc in circuits:
    qc.h(0)
    qc.measure_all()

sampler = Sampler()
result = sampler.run(circuits).result()

for i, qc in enumerate(circuits):
    data = result.quasi_dists[i]  # CORRECT
    print(data)