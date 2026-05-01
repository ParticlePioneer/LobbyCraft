import statistics 
from dal import queue_dal, match_dal, session_dal 
from dal.player_dal import get_player 
from models.entities import MatchParticipant 
 
def _seed_mmr(mode_id): 
    from db.connection import get_conn 
    sql = '''SELECT AVG(p.current_mmr) 
             FROM QUEUE q 
             JOIN PARTY_MEMBER pm ON pm.party_id=q.party_id 
             JOIN PLAYER p ON p.player_id=pm.player_id 
             WHERE q.status='WAITING' AND q.mode_id=:1''' 
    with get_conn() as conn: 
        cur = conn.cursor() 
        cur.execute(sql, [mode_id]) 
        val = cur.fetchone()[0] 
    return float(val) if val else 1000.0 
 
def assemble_lobby(mode, criteria, session_id, region): 
    '''Returns match_id if lobby assembled, else None.''' 
    parties = queue_dal.get_waiting_parties( 
        mode_id=mode.mode_id, 
        seed_mmr=_seed_mmr(mode.mode_id), 
        max_diff=criteria.max_mm_diff, 
    ) 
    required = mode.max_players // mode.team_size 
    if len(parties) < required: 
        return None 
    selected = sorted(parties[:required], key=lambda p: p.avg_mmr) 
    lobby_mmr = round(statistics.mean(p.avg_mmr for p in selected)) 
    match = match_dal.create_match( 
        session_id=session_id, mode_id=mode.mode_id, 
        region=region, match_mmr=lobby_mmr) 
    participants = [] 
    for i, party in enumerate(selected): 
        team = match_dal.create_team( 
            match_id=match.match_id, 
            team_number=i + 1, 
            avg_team_mmr=round(party.avg_mmr)) 
        for pid in party.player_ids: 
            player = get_player(pid) 
            participants.append(MatchParticipant( 
                player_id=pid, match_id=match.match_id, team_id=team.team_id, 
                placement=0, survival_time=0, kills=0, assists=0, revives=0, 
                damage_done=0, damage_taken=0, is_winner=0, 
                mmr_before=player.current_mmr, mmr_delta=0)) 
    match_dal.bulk_insert_participants(participants) 
    queue_dal.mark_matched([p.queue_no for p in selected]) 
    session_dal.complete_session(session_id) 
    return match.match_id 