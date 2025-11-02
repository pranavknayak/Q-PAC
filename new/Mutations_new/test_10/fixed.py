for idx, circ in enumerate(circuits):
    shot_count = ret.shots_list[idx]
    run_experiment(circ, shot_count)
