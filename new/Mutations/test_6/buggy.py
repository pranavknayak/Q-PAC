for circuit in circuits:
    # WRONG: always using ret.quasi_dists[0]
    counts = {
        np.binary_repr(k, circuit.num_qubits): round(v * shots)
        for k, v in ret.quasi_dists[0].items()
    }
    results.append(counts)
