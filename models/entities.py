from dataclasses import dataclass 
from datetime import date, datetime 
from typing import Optional 
 
@dataclass 
class SystemRole: 
    sys_role_id: int 
    sys_role_name: str 
 
@dataclass 
class Role: 
    role_id: int 
    role_name: str 
 
@dataclass 
class GameMode: 
    mode_id: int 
    mode_name: str 
    team_size: int 
    max_players: int 
    mode_type: str 
 
@dataclass 
class Player: 
    player_id: int 
    username: str 
    region: str 
    join_date: date 
    current_mmr: int 
    sys_role_id: int 
 
@dataclass 
class Party: 
    party_id: int 
    created_at: datetime 
    party_type: str 
 
@dataclass 
class PartyMember: 
    party_id: int 
    player_id: int 
    member_role: Optional[str] = None 
 
@dataclass 
class RolePreference: 
    player_id: int 
    role_id: int 
    priority: int 
 
@dataclass 
class MatchmakingCriteria: 
    criteria_id: int 
    max_mm_diff: int 
    max_wait_time: int 
    priority_type: str 
    mode_id: int 

@dataclass 
class MatchmakingSession: 
    session_id: int 
    start_time: datetime 
    end_time: Optional[datetime] 
    status: str 
    criteria_id: int 
 
@dataclass 
class QueueEntry: 
    queue_no: int 
    queue_type: str 
    enqueue_time: datetime 
    party_id: int 
    mode_id: int 
    status: str 
 
@dataclass 
class Match: 
    match_id: int 
    match_region: str 
    status: str 
    m_start_time: datetime 
    m_end_time: Optional[datetime] 
    match_mmr: int 
    session_id: int 
    mode_id: int 
 
@dataclass 
class Team: 
    team_id: int 
    match_id: int 
    team_number: int 
    avg_team_mmr: int 
 
@dataclass 
class MatchParticipant: 
    player_id: int 
    match_id: int 
    team_id: int 
    placement: int 
    survival_time: int 
    kills: int 
    assists: int 
    revives: int 
    damage_done: int 
    damage_taken: int 
    is_winner: int 
    mmr_before: int 
    mmr_delta: int 
    role_used: Optional[str] = None 
 
# Engine composites 
@dataclass 
class PartyWithMMR: 
    queue_no: int 
    party_id: int 
    player_ids: list 
    avg_mmr: float 
    enqueue_time: datetime 
 
@dataclass 
class LobbyTeam: 
    team_number: int 
    player_ids: list 
    avg_team_mmr: float 

