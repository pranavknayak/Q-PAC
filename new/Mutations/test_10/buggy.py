# Shots per circuit returned in ret.shots_list
for circ in circuits:
    shot_count = ret.shots_list[2]  # WRONG: always takes the 3rd entry
    run_experiment(circ, shot_count)
