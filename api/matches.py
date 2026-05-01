from fastapi import APIRouter, HTTPException 
from pydantic import BaseModel 
from dal import match_dal 
from dal.player_dal import update_mmr 
from engine.mmr import compute_delta 
from db.connection import get_conn 
 
router = APIRouter() 
 
class ParticipantResult(BaseModel): 
    player_id: int 
    placement: int 
    survival_time: int 
    kills: int 
    assists: int 
    revives: int 
    damage_done: int 
    damage_taken: int 
    is_winner: int 
    role_used: str = None 
 
class MatchResult(BaseModel): 
    participants: list 
 
@router.get('/{match_id}') 
def get_match(match_id: int): 
    m = match_dal.get_match(match_id) 
    if not m: raise HTTPException(404, 'Match not found') 
    return m.__dict__ 

@router.get('/{match_id}/participants')
def get_participants(match_id: int):
    return match_dal.get_match_participants(match_id)
 
@router.post('/{match_id}/result') 
def submit_result(match_id: int, body: MatchResult): 
    total = len(body.participants) 
    with get_conn() as conn: 
        cur = conn.cursor() 
        cur.execute('SELECT AVG(mmr_before) FROM MATCH_PARTICIPANT WHERE match_id=:1', [match_id]) 
        lobby_avg = float(cur.fetchone()[0] or 1000) 
    for p in body.participants: 
        with get_conn() as conn: 
            cur = conn.cursor() 
            cur.execute('SELECT mmr_before FROM MATCH_PARTICIPANT WHERE match_id=:1 AND player_id=:2', 
                        [match_id, p.player_id]) 
            row = cur.fetchone() 
        mmr_before = int(row[0]) if row else 1000 
        delta = compute_delta( 
            player_mmr=mmr_before, opponent_avg_mmr=lobby_avg, 
            won=bool(p.is_winner), placement=p.placement, total_players=total) 
        match_dal.update_participant_result( 
            match_id=match_id, player_id=p.player_id, 
            placement=p.placement, survival_time=p.survival_time, 
            kills=p.kills, assists=p.assists, revives=p.revives, 
            damage_done=p.damage_done, damage_taken=p.damage_taken, 
            is_winner=p.is_winner, mmr_delta=delta, role_used=p.role_used) 
        update_mmr(p.player_id, delta) 
    match_dal.finalise_match(match_id) 
    return {'status': 'finalised', 'match_id': match_id} 
 
@router.get('/{match_id}/lobby-quality') 
def lobby_quality(match_id: int): 
    sql = '''SELECT t.match_id, 
                    COUNT(t.team_id)                         AS team_count, 
                    ROUND(AVG(t.avg_team_mmr),2)             AS lobby_avg_mmr, 
                    ROUND(STDDEV(t.avg_team_mmr),2)          AS mmr_std_dev, 
                    MAX(t.avg_team_mmr)-MIN(t.avg_team_mmr)  AS mmr_spread 
             FROM   TEAM t WHERE t.match_id=:1 GROUP BY t.match_id''' 
    with get_conn() as conn: 
        cur = conn.cursor() 
        cur.execute(sql, [match_id]) 
        cols = [d[0].lower() for d in cur.description] 
        row = cur.fetchone() 
    return dict(zip(cols, row)) if row else {}

 
@router.get('/leaderboard/kills') 
def leaderboard(mode_type: str = 'battle_royale', limit: int = 10): 
    sql = '''SELECT p.username, 
                    SUM(mp.kills)                               AS total_kills, 
                    COUNT(mp.match_id)                          AS matches_played, 
                    ROUND(SUM(mp.kills)/COUNT(mp.match_id),2)   AS avg_kills 
             FROM   MATCH_PARTICIPANT mp 
             JOIN   PLAYER p     ON p.player_id=mp.player_id 
             JOIN   MATCH m      ON m.match_id=mp.match_id 
             JOIN   GAME_MODE gm ON gm.mode_id=m.mode_id 
             WHERE  gm.mode_type=:1 
             AND    m.m_start_time >= ADD_MONTHS(SYSDATE,-1) 
             GROUP  BY p.username 
             ORDER  BY total_kills DESC 
             FETCH  FIRST :2 ROWS ONLY''' 
    with get_conn() as conn: 
        cur = conn.cursor() 
        cur.execute(sql, [mode_type, limit]) 
        cols = [d[0].lower() for d in cur.description] 
        return [dict(zip(cols, r)) for r in cur.fetchall()] 
