K_FACTOR = 32   # max MMR swing per match 
def expected_score(player_mmr, opponent_avg_mmr): 
    return 1.0 / (1.0 + 10 ** ((opponent_avg_mmr - player_mmr) / 400)) 
def compute_delta(player_mmr, opponent_avg_mmr, won, placement, total_players): 
    if total_players > 10:          # battle royale 
        if placement == 1: 
            actual = 1.0 
        elif placement <= max(1, total_players // 10): 
            actual = 0.75 
        else: 
            actual = max(0.0, 1.0 - placement / total_players) 
    else:                           # competitive 
        actual = 1.0 if won else 0.0 
    exp = expected_score(float(player_mmr), opponent_avg_mmr) 
    return max(-50, min(50, round(K_FACTOR * (actual - exp)))) 