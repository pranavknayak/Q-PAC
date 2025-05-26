# Correct: Use transpilation to optimize gates and maintain unitarity
qc = transpile(qc, optimization_level=3)