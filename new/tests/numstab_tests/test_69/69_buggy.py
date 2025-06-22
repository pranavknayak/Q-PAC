#FP
import numpy as np

def deterministic_op(x): # doesn't change output with invariant input, no point in performing estimation
    pass

sample1 = deterministic_op(1)
sample2 = deterministic_op(1)

minimum = np.min([sample1, sample2])
