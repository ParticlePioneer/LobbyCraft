from abc import ABC, abstractmethod


class BaseMatchmakingEngine(ABC):
    """
    Contract every matchmaking engine must satisfy.
    The orchestrator in matchmaker.py calls these three methods
    in order and never contains algorithm logic itself.
    """

    def __init__(self, criteria, params: dict = None,
                 rating_engine=None):
        """
        criteria     : MatchmakingCriteria dataclass instance
        params       : dict loaded from ENGINE_PARAMETER table
        rating_engine: BaseRatingEngine instance for delta computation
        """
        self.criteria      = criteria
        self.params        = params or {}
        self.rating_engine = rating_engine

    @abstractmethod
    def get_candidates(self, mode_id: int, region: str) -> list:
        """
        Query QUEUE and return a list of PartyWithMMR objects
        that are eligible according to this engine's rules.
        Ordered oldest-first to prevent queue starvation.
        """
        pass

    @abstractmethod
    def select_and_form_teams(self, candidates: list,
                               mode) -> list | None:
        """
        From the eligible candidates, pick exactly the required
        number of parties and return a list of LobbyTeam objects.
        Returns None if a full lobby cannot be formed.
        """
        pass

    @abstractmethod
    def compute_lobby_mmr(self, teams: list) -> int:
        """
        Given the formed teams, return the single integer MMR
        value to stamp on the MATCH record.
        """
        pass