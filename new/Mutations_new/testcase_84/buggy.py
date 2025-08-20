# Incorrect: Multiple gates resulting in numerical instability
qc.rx(math.pi / 3, qr[0])
qc.ry(math.pi / 4, qr[0])
qc.rz(math.pi / 5, qr[0])
# Combined operation becomes non-unitary due to floating-point inaccuracies