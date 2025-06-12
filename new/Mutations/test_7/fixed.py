circuits = [make_circuit(p) for p in params]
# ensure same length
assert len(ret.results) == len(circuits)
for idx in range(len(circuits)):
    outcome = execute(circuits[idx], shots)
    log.append(outcome)
