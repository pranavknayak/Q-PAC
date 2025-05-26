# build a vector of N circuits
circuits = [make_circuit(p) for p in params]
# then later assume M results
for i in range(len(ret.results)):  
    outcome = execute(circuits[i], shots)
    log.append(outcome)
