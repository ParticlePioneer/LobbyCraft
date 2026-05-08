from engine.base_rating import BaseRatingEngine
from engine.scoring import placement_score, winloss_score


class EloRating(BaseRatingEngine):
    """
    Standard ELO-style rating with configurable K factor.

    Supports both battle royale (placement-based actual score)
    and competitive (win/loss binary actual score).

    The expected score formula follows the standard ELO model:
        E = 1 / (1 + 10^((opponent_mmr - player_mmr) / 400))

    Delta = K * (actual - expected), clamped to [-delta_cap, +delta_cap]
    """

    def __init__(
        self,
        k_factor: int = 32,
        delta_cap: int = 50,
        mmr_floor: int = 0,
        mode_type: str = 'battle_royale',
    ):
        """
        k_factor   : max MMR swing per match.
                     Lower = more stable ratings (use 24 for ranked).
                     Higher = faster convergence (use 32 for casual).
        delta_cap  : hard clamp on single-match MMR gain or loss.
        mmr_floor  : minimum MMR a player can drop to (enforced in DAL).
        mode_type  : 'battle_royale' uses placement_score.
                     'competitive'  uses winloss_score.
        """
        self.k_factor  = k_factor
        self.delta_cap = delta_cap
        self.mmr_floor = mmr_floor
        self.mode_type = mode_type

    def _expected_score(self, player_mmr: float,
                        opponent_avg_mmr: float) -> float:
        """
        ELO expected score: probability of outperforming the
        opponent pool given the current MMR gap.
        Returns a value between 0.0 and 1.0.
        """
        return 1.0 / (
            1.0 + 10 ** ((opponent_avg_mmr - player_mmr) / 400)
        )

    def _actual_score(self, won: bool, placement: int,
                      total_players: int) -> float:
        """
        Convert match outcome to actual score based on mode type.
        """
        if self.mode_type == 'battle_royale':
            return placement_score(placement, total_players)
        return winloss_score(won)

    def compute_delta(
        self,
        player_mmr: int,
        opponent_avg_mmr: float,
        won: bool,
        placement: int,
        total_players: int,
    ) -> int:
        """
        Compute ELO MMR delta for one player after one match.

        Steps:
          1. Compute actual score from match outcome.
          2. Compute expected score from MMR gap.
          3. Delta = K * (actual - expected).
          4. Clamp to [-delta_cap, +delta_cap].
          5. Return as integer.
        """
        actual   = self._actual_score(won, placement, total_players)
        expected = self._expected_score(
            float(player_mmr), opponent_avg_mmr)
        raw = round(self.k_factor * (actual - expected))
        return max(-self.delta_cap, min(self.delta_cap, raw))

    def initial_mmr(self) -> int:
        return 1000