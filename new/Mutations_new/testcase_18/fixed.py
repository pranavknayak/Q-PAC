# fixed version
grover_circuit = initialize_s(grover_circuit, [0, 1])
grover_circuit.cz(q[0], q[1])
grover_circuit.h([0, 1])
grover_circuit.z([0, 1])
grover_circuit.cz(q[0], q[1])
grover_circuit.h([0, 1])
grover_circuit.measure([0, 1], [0, 1])