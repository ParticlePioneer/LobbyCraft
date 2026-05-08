from engine.base_rating import BaseRatingEngine
from engine.scoring import placement_score, winloss_score
import math


class Glicko2Rating(BaseRatingEngine):
    """
    Glicko-2 rating system stub.
    Glicko-2 improves on ELO by tracking two additional values
    per player:
      - Rating Deviation (RD): confidence in the rating.
        High RD = uncertain. Low RD = well-established.
      - Volatility (σ): consistency of the player's performance.
        High volatility = unpredictable player.

    Full Glicko-2 requires RD and volatility columns on PLAYER.
    Until those columns are added to the schema, this class falls
    back to an ELO approximation with Glicko-2 initial values.
    Conventional Glicko-2 starts players at MMR=1500, RD=350, vol=0.06.
    """

    def __init__(
        self,
        tau: float = 0.5,
        initial_rd: float = 350.0,
        initial_vol: float = 0.06,
        delta_cap: int = 50,
    ):
        """
        tau         : system constant controlling volatility change.
                      Typically between 0.3 and 1.2.
        initial_rd  : starting rating deviation for new players.
        initial_vol : starting volatility for new players.
        delta_cap   : hard clamp on single-match delta.
        """
        self.tau         = tau
        self.initial_rd  = initial_rd
        self.initial_vol = initial_vol
        self.delta_cap   = delta_cap

    def _glicko_scale(self, mmr: int) -> float:
        """Convert standard MMR to Glicko-2 internal scale (μ)."""
        return (mmr - 1500) / 173.7178

    def _rd_scale(self, rd: float) -> float:
        """Convert RD to Glicko-2 internal scale (φ)."""
        return rd / 173.7178

    def _g(self, phi: float) -> float:
        """Glicko-2 g function."""
        return 1.0 / math.sqrt(1 + 3 * phi**2 / math.pi**2)

    def _expected(self, mu: float, mu_j: float,
                  phi_j: float) -> float:
        """Glicko-2 expected score against one opponent."""
        return 1.0 / (1.0 + math.exp(-self._g(phi_j) * (mu - mu_j)))

    def compute_delta(self,player_mmr: int,opponent_avg_mmr: float,won: bool,placement: int,total_players: int,) -> int:
        'Simplified Glicko-2 single-opponent approximation.'
        mu   = self._glicko_scale(player_mmr)
        mu_j = self._glicko_scale(int(opponent_avg_mmr))
        phi_j = self._rd_scale(self.initial_rd)

        if total_players > 10:
            actual = placement_score(placement, total_players)
        else:
            actual = 1.0 if won else 0.0

        expected = self._expected(mu, mu_j, phi_j)
        g_val    = self._g(phi_j)

        # Simplified update (full update needs iterative volatility step)
        phi_player = self._rd_scale(self.initial_rd)
        v = 1.0 / (g_val**2 * expected * (1 - expected))
        delta_internal = v * g_val * (actual - expected)

        # Convert back from internal scale to MMR points
        raw = round(delta_internal * 173.7178 / phi_player)
        return max(-self.delta_cap, min(self.delta_cap, raw))

    def initial_mmr(self) -> int:
        # Glicko-2 conventionally starts at 1500
        return 1500