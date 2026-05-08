"""
Shared scoring converters used by all rating engines.
Converts raw match outcomes into a normalised actual score
between 0.0 and 1.0 for use in ELO-style delta formulas.

These functions have no database dependency and are fully
unit-testable without a running Oracle instance.
"""


def placement_score(placement: int, total_players: int) -> float:
    """
    Battle royale placement → normalised score.

    Scoring bands:
      1st place       → 1.0   (winner bonus)
      Top 10%         → 0.75  (strong performance)
      Everyone else   → linear decay from 0.75 toward 0.0

    Args:
        placement     : final rank in the match (1 = best)
        total_players : total number of players in the lobby

    Returns:
        float between 0.0 and 1.0
    """
    if placement <= 0 or total_players <= 0:
        return 0.0
    if placement == 1:
        return 1.0
    top_10_pct = max(1, total_players // 10)
    if placement <= top_10_pct:
        return 0.75
    return max(0.0, 1.0 - placement / total_players)


def winloss_score(won: bool) -> float:
    """
    Competitive binary outcome → score.

    Args:
        won : True if the player's team won the match

    Returns:
        1.0 for a win, 0.0 for a loss
    """
    return 1.0 if won else 0.0


def blended_score(won: bool, placement: int,
                  total_players: int,
                  placement_weight: float = 0.6) -> float:
    """
    Blended score combining win/loss and placement.
    Useful for hybrid modes where both matter.

    Args:
        won               : whether the player's team won
        placement         : final rank
        total_players     : lobby size
        placement_weight  : how much placement influences the score
                            (0.0 = pure win/loss, 1.0 = pure placement)

    Returns:
        float between 0.0 and 1.0
    """
    p_score = placement_score(placement, total_players)
    w_score = winloss_score(won)
    return (placement_weight * p_score
            + (1.0 - placement_weight) * w_score)