import numpy as np
z = 1
z = z / abs(z)
u_error = np.array([[1, 0], [0, z]])
noise_params = {'U':
    {'gate_time': 1,
     'p_depol': 0.001,
     'p_pauli': [0, 0, 0.01],
     'U_error': u_error}
}