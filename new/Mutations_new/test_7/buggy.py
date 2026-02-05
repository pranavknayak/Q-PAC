from qiskit import QuantumCircuit
from qiskit.primitives import Sampler

circuits = []
for i in range(4):
    qc = QuantumCircuit(2)
    qc.rx(i * 0.5, 0)
    qc.measure_all()
    circuits.append(qc)

sampler = Sampler()
result = sampler.run(circuits).result()

for i in range(4):
    counts = result.quasi_dists[i + 1]  # WRONG: off by one
    print(f"Circuit {i}: {counts}")