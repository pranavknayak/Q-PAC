'''
The following code-pair contains an IncorrectUnitaryMatrix bug.
'''

correctCode = '''
# Correct: Normalize the rotation angle
qc.rx(4 * math.pi % (2 * math.pi), qr[4])
'''

buggyCode = '''
# Incorrect: Over-rotation resulting in non-unitary behavior
qc.rx(4 * math.pi, qr[4])  # Rotation angle exceeds the valid range
'''
