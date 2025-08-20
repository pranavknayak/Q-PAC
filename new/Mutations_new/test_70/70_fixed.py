#FN: QPAC can't recognize sizes when iterables aren't directly initialized

def sampling(x): # return samples from some distribution
    pass

average_estimate = [sampling(i) for i in range(10)]
