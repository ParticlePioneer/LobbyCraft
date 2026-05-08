import statistics
from engine.base_engine import BaseMatchmakingEngine
from engine.flat_rating import FlatRating
from models.entities import LobbyTeam


class BucketEngine(BaseMatchmakingEngine):
    """
    Bucket-based matchmaking engine.

    Candidate selection:
        Fetches ALL waiting parties for the mode with no MMR
        tolerance filter. The engine handles grouping itself.

    Team formation:
        Assigns each party to a bucket:
            bucket_number = floor(avg_mmr / bucket_size)
        Finds the first bucket (lowest MMR) that contains enough
        parties to fill a lobby. Allows cross-bucket matching if
        adjacent buckets are within bucket_overlap of each other.

    Use case:
        Casual / unranked modes where you want fast queue times
        over strict MMR fairness. Players within 250 MMR of each
        other are considered fair enough.

    Rating engine:
        Defaults to FlatRating because casual modes should give
        predictable, stable MMR rewards not tied to opponent strength.
    """

    def __init__(self, criteria, params: dict = None,rating_engine=None):
        super().__init__(criteria, params, rating_engine)
        if self.rating_engine is None:
            self.rating_engine = FlatRating(
                win_delta=self.params.get('win_delta', 20),
                loss_delta=self.params.get('loss_delta', -15),
                delta_cap=self.params.get('delta_cap', 30),
                mode_type='battle_royale',
            )
        self.bucket_size = self.params.get('bucket_size', 250)
        self.overlap     = self.params.get('bucket_overlap', 50)

    def get_candidates(self, mode_id: int, region: str) -> list:
        """
        Returns ALL waiting parties for this mode.
        No MMR filter applied; bucketing happens in
        select_and_form_teams.
        """
        from dal.queue_dal import get_waiting_parties_all
        return get_waiting_parties_all(mode_id)

    def _assign_bucket(self, avg_mmr: float) -> int:
        return int(avg_mmr // self.bucket_size)

    def _buckets_compatible(self, b1: int, b2: int) -> bool:
        """
        Two buckets are compatible if the MMR boundary between
        them is within the overlap threshold.
        Adjacent buckets (diff of 1) are always compatible.
        """
        return abs(b1 - b2) <= 1
    
    def select_and_form_teams(self, candidates: list,mode) -> list | None:
        
        required = mode.max_players // mode.team_size

        bucketed: dict[int, list] = {}
        for party in candidates:
            bucket = self._assign_bucket(party.avg_mmr)
            bucketed.setdefault(bucket, []).append(party)

        # Find the first viable bucket (sorted ascending = lowest MMR first)
        for bucket_id, parties in sorted(bucketed.items()):
            # Also pull in adjacent compatible buckets if needed
            pool = list(parties)
            for other_id, other_parties in bucketed.items():
                if other_id != bucket_id and \
                   self._buckets_compatible(bucket_id, other_id):
                    pool.extend(other_parties)

            if len(pool) >= required:
                selected = sorted(
                    pool[:required], key=lambda p: p.avg_mmr)
                return [
                    LobbyTeam(
                        team_number=i + 1,
                        player_ids=party.player_ids,
                        avg_team_mmr=round(party.avg_mmr),
                        queue_no=party.queue_no,
                    )
                    for i, party in enumerate(selected)
                ]
        return None

    def compute_lobby_mmr(self, teams: list) -> int:
        """Overall lobby MMR is the mean of all team MMRs."""
        return round(statistics.mean(t.avg_team_mmr for t in teams))