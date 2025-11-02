decoded = []
for idx, circuit in enumerate(circuits):
    # FIXED: ret.measurements[idx]
    counts = {
        k: v for k, v in ret.measurements[idx].items()
    }
    decoded.append(counts)