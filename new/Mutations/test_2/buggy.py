# Incorrect: Over-rotation resulting in non-unitary behavior
qc.rx(4 * math.pi, qr[4])  # Rotation angle exceeds the valid range