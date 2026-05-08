import statistics
from engine.base_engine import BaseMatchmakingEngine
from engine.elo_rating import EloRating
from models.entities import LobbyTeam


class MMREngine(BaseMatchmakingEngine):
    """
    MMR-based matchmaking engine.

    Candidate selection:
        Fetches all WAITING parties whose average MMR falls within
        max_mm_diff of the current lobby seed MMR.
        Seed MMR = average MMR of all currently waiting players
        in this mode. This centres the tolerance window on the
        actual waiting population rather than a fixed value.

    Team formation:
        Sorts selected parties by avg_mmr ascending and assigns
        each party to a sequential team slot.
        One party fills one team slot.

    Lobby MMR:
        Mean of all team MMRs.
    """

    def __init__(self, criteria, params: dict = None,
                 rating_engine=None):
        super().__init__(criteria, params, rating_engine)
        # Fall back to EloRating if no rating engine injected
        if self.rating_engine is None:
            self.rating_engine = EloRating(
                k_factor=self.params.get('k_factor', 32),
                delta_cap=self.params.get('delta_cap', 50),
                mmr_floor=self.params.get('mmr_floor', 0),
                mode_type='battle_royale',
            )

    def _seed_mmr(self, mode_id: int) -> float:
        """
        Average MMR of all players currently WAITING in this mode.
        Returns 1000.0 as default if queue is empty.
        """
        from db.connection import get_conn
        sql = '''
            SELECT AVG(p.current_mmr)
            FROM   QUEUE q
            JOIN   PARTY_MEMBER pm ON pm.party_id  = q.party_id
            JOIN   PLAYER p        ON p.player_id  = pm.player_id
            WHERE  q.status  = 'WAITING'
            AND    q.mode_id = :1
        '''
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute(sql, [mode_id])
            val = cur.fetchone()[0]
        return float(val) if val else 1000.0

    def get_candidates(self, mode_id: int, region: str) -> list:
        """
        Returns WAITING parties within max_mm_diff of seed MMR.
        Ordered oldest-first (enqueue_time ASC).
        """
        from dal.queue_dal import get_waiting_parties
        seed     = self._seed_mmr(mode_id)
        max_diff = self.params.get(
            'max_mmr_diff', self.criteria.max_mm_diff)
        return get_waiting_parties(
            mode_id=mode_id,
            seed_mmr=seed,
            max_diff=max_diff,
        )

    def select_and_form_teams(self, candidates: list,
                               mode) -> list | None:
        """
        Sort by avg_mmr, take exactly (max_players // team_size)
        parties, assign one party per team slot.
        Returns None if not enough candidates.
        """
        required = mode.max_players // mode.team_size
        if len(candidates) < required:
            return None

        selected = sorted(
            candidates[:required], key=lambda p: p.avg_mmr)

        return [
            LobbyTeam(
                team_number=i + 1,
                player_ids=party.player_ids,
                avg_team_mmr=round(party.avg_mmr),
                queue_no=party.queue_no,
            )
            for i, party in enumerate(selected)
        ]

    def compute_lobby_mmr(self, teams: list) -> int:
        """Overall lobby MMR is the mean of all team MMRs."""
        return round(statistics.mean(t.avg_team_mmr for t in teams))