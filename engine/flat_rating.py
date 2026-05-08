from engine.base_rating import BaseRatingEngine
from engine.scoring import placement_score, winloss_score


class FlatRating(BaseRatingEngine):
    """
    Simple flat-delta rating engine.

    No expected score calculation — awards fixed gain/loss values
    regardless of opponent strength. Useful for:
      - Casual / unranked modes where predictable MMR movement
        matters more than accuracy.
      - Early testing before ELO parameters are tuned.
      - Modes where the MMR gap between players is intentionally
        wide (open lobbies).

    Battle royale: scales the win_delta by placement_score so
    first place gets the full delta and last place gets near zero.
    Competitive: flat win_delta for wins, loss_delta for losses.
    """

    def __init__(
        self,
        win_delta: int = 20,
        loss_delta: int = -15,
        delta_cap: int = 30,
        mode_type: str = 'competitive',
    ):
        """
        win_delta  : MMR gained on a win (or 1st place in BR).
        loss_delta : MMR lost on a loss (negative integer).
        delta_cap  : hard clamp (should be >= win_delta).
        mode_type  : 'battle_royale' or 'competitive'.
        """
        self.win_delta  = win_delta
        self.loss_delta = loss_delta
        self.delta_cap  = delta_cap
        self.mode_type  = mode_type

    def compute_delta(
        self,
        player_mmr: int,
        opponent_avg_mmr: float,
        won: bool,
        placement: int,
        total_players: int,
    ) -> int:
        """
        Compute flat MMR delta.

        Battle royale: delta = win_delta * placement_score
          so 1st place gains win_delta, last place gains ~0.
        Competitive:   delta = win_delta if won, else loss_delta.
        """
        if self.mode_type == 'battle_royale':
            score = placement_score(placement, total_players)
            raw   = round(self.win_delta * score)
        else:
            raw = self.win_delta if won else self.loss_delta
        return max(-self.delta_cap, min(self.delta_cap, raw))

    def initial_mmr(self) -> int:
        return 1000