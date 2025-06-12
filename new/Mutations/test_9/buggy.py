# ret.data has one entry per circuit
for i, (c, d) in enumerate(zip(circuits, ret.data[1:])):  
    # misaligned: skipping the first result
    process(c, d)
