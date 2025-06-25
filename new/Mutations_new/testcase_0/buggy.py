# buggy version
grover_circuit.measure_all()  # Incorrect placement of the measurement
grover_circuit.cz(0,1)  # Oracle
grover_circuit.h([0,1])
grover_circuit.z([0,1])
grover_circuit.cz(0,1)
grover_circuit.h([0,1])