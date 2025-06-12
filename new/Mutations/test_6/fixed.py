for idx, circuit in enumerate(circuits):
    # FIXED: ret.quasi_dists[idx]
    counts = {
        np.binary_repr(k, circuit.num_qubits): round(v * shots)
        for k, v in ret.quasi_dists[idx].items()
    }
    results.append(counts)
