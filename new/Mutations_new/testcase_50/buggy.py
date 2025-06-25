# buggy version
# Incorrect: Overlapping registers used in the subcircuit
circuit_2mod15(qc, qr[:3], cr[:1])  # Using a subset of the registers, causing overlap"