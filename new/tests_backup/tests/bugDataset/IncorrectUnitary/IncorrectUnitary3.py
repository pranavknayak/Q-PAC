'''
The following code-pair contains an IncorrectUnitaryMatrix bug.
'''

correctCode = '''
# Correct: Use transpilation to optimize gates and maintain unitarity
qc = transpile(qc, optimization_level=3)
'''

buggyCode = '''
# Incorrect: Multiple gates resulting in numerical instability
qc.rx(math.pi / 3, qr[0])
qc.ry(math.pi / 4, qr[0])
qc.rz(math.pi / 5, qr[0])
# Combined operation becomes non-unitary due to floating-point inaccuracies
'''
