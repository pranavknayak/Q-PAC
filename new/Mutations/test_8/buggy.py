# ret.measurements is a list of dicts, one per circuit
decoded = []
for circuit in circuits:
    # WRONG: uses the loop variable ‘circuit’ to index ret.measurements
    counts = {
        k: v for k, v in ret.measurements[circuit].items()
    }
    decoded.append(counts)
