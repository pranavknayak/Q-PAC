'''
The following code-pair contains an IncorrectUnitaryMatrix bug.
'''

correctCode = '''
import numpy as np
from qiskit.providers.aer.noise import NoiseModel, amplitude_damping_error

# Correct: Complete Kraus operators for amplitude damping
kraus_ops = [
    np.array([[1, 0], [0, np.sqrt(0.9)]]),  # Valid Kraus operator
    np.array([[0, 0], [np.sqrt(0.1), 0]])   # Ensures CPTP completeness
]
noise_model = NoiseModel()
noise_model.add_all_qubit_quantum_error(amplitude_damping_error(kraus_ops), 'u1')
'''

buggyCode = '''
import numpy as np
from qiskit.providers.aer.noise import NoiseModel, amplitude_damping_error

# Incorrect: Incomplete Kraus operators for amplitude damping
kraus_ops = [
    np.array([[1, 0], [0, 0.9]]),  # Valid Kraus operator
    np.array([[0, 0], [0.3, 0]])  # Missing the third Kraus operator for CPTP map
]
noise_model = NoiseModel()
noise_model.add_all_qubit_quantum_error(amplitude_damping_error(kraus_ops), 'u1')
'''
