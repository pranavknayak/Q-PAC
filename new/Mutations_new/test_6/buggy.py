import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.primitives import Sampler

shots = 10
qc1 = QuantumCircuit(2)
qc1.h(0)
qc1.measure_all()

qc2 = QuantumCircuit(2)
qc2.h(1)
qc2.measure_all()

qc3 = QuantumCircuit(2)
qc3.h([0, 1])
qc3.measure_all()

circuits = [qc1, qc2, qc3]
results = []

sampler = Sampler()
job = sampler.run(circuits)
ret = job.result()

for circuit in circuits:
    # WRONG: always using ret.quasi_dists[0]
    counts = {
        np.binary_repr(k, circuit.num_qubits): round(v * shots)
        for k, v in ret.quasi_dists[0].items()
    }
    results.append(counts)
