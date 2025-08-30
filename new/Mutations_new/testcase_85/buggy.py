import numpy as np
from qiskit_aer.noise import NoiseModel, amplitude_damping_error, QuantumError
from qiskit.quantum_info import Kraus
# Incorrect: Incomplete Kraus operators for amplitude damping
kraus_ops = [
    np.array([[1, 0], [0, 0.9]]),  # Valid Kraus operator
    np.array([[0, 0], [0.3, 0]])  # Missing the third Kraus operator for CPTP map
]
kraus_channel = Kraus(kraus_ops)
kraus_error = QuantumError(kraus_channel)

# Add to noise model
noise_model = NoiseModel()
noise_model.add_all_qubit_quantum_error(kraus_error, 'u1')
