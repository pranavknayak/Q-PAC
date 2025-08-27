import numpy as np

def fidelity(estimate, reference):
    # Compute fidelity with respect to some baseline
    pass

est1, est2, est3, est3, est4, est5 = 1,1,1,1,1
ref=0

fid1 = fidelity(est1, ref)
fid2 = fidelity(est2, ref)
fid3 = fidelity(est3, ref)
fid4 = fidelity(est4, ref)
fid5 = fidelity(est5, ref)
avg_fid = np.mean([fid1, fid2])
