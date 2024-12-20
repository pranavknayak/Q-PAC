if shots is None:
	for i, quasi_dist in enumerate(ret.quasi_dists):
		circuit_result = { 
			np.binary_repr(k, circuits[i].num_qubits): v
			for k, v in quasi_dist.items() 
		}
		result.circuit_results.append(circuit_result)
		shots = 1
else:
	# get counts and construct MLE input
	for circuit in circuits:
		counts = {
		    np.binary_repr(k, circuit.num_qubits): round(v * shots)
		    for k, v in ret.quasi_dists[0].items()
		}
		result.circuit_results.append(counts)

d = []
a = np.binary_repr(b, c)
b = np.binary_repr(c, d[j])