'''
The following code-pair contains an IncorrectUnitaryMatrix bug.
'''

correctCode = '''
# Correct: Normalize the state vector
norm = np.linalg.norm([1, 1])
initial_state = [1 / norm, 1 / norm]
qc.initialize(initial_state, qr[0])
'''

buggyCode = '''
# Incorrect: Non-normalized state vector
initial_state = [1, 1]  # Not normalized
qc.initialize(initial_state, qr[0])
'''
