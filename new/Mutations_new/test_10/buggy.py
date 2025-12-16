from qiskit import QuantumCircuit
from qiskit.primitives import Sampler

qc1 = QuantumCircuit(1)
qc1.h(0)
qc1.measure_all()

qc2 = QuantumCircuit(1)
qc2.x(0)
qc2.measure_all()

qc3 = QuantumCircuit(1)
qc3.y(0)
qc3.measure_all()

circuits = [qc1, qc2, qc3]  # 3 circuits

sampler = Sampler()
result = sampler.run(circuits).result()

# WRONG: range(2) only processes 2 circuits, but we have 3
for i in range(2):
    print(result.quasi_dists[i])