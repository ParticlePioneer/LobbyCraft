# engine/base_rating.py
from abc import ABC, abstractmethod

class BaseRatingEngine(ABC):
    """
    Contract every rating formula must satisfy.
    A matchmaking engine (MMREngine, BucketEngine etc.) holds a
    reference to one RatingEngine and calls compute_delta after
    each match.
    """

    @abstractmethod
    def compute_delta(
        self,
        player_mmr: int,
        opponent_avg_mmr: float,
        won: bool,
        placement: int,
        total_players: int,
    ) -> int:
        """
        Returns the integer MMR change for one player after one match.
        Positive = gained MMR, negative = lost MMR.
        """
        pass

    @abstractmethod
    def initial_mmr(self) -> int:
        """
        Returns the starting MMR for a newly registered player.
        Allows different engines to start at different baseline values.
        """
        pass