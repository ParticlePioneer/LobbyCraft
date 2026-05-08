from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dal import match_dal
from dal.player_dal import update_mmr
from db.connection import get_conn
from models.entities import MatchmakingCriteria
from engine.loader import load_engine_for_mode

router = APIRouter()

class ParticipantResult(BaseModel):
    player_id:     int
    placement:     int
    survival_time: int
    kills:         int
    assists:       int
    revives:       int
    damage_done:   int
    damage_taken:  int
    is_winner:     int
    role_used:     str = None

class MatchResult(BaseModel):
    participants: list

@router.get('/{match_id}')
def get_match(match_id: int):
    m = match_dal.get_match(match_id)
    if not m:
        raise HTTPException(404, 'Match not found')
    data = m.__dict__.copy()

    # Add mode metadata for UI cards.
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            'SELECT mode_name, mode_type FROM GAME_MODE WHERE mode_id=:1',
            [m.mode_id]
        )
        mode_row = cur.fetchone()
    if mode_row:
        data['mode_name'] = mode_row[0]
        data['mode_type'] = mode_row[1]

    # Attach winner and participant payloads used by "Load Match Info" screen.
    data['winner_info'] = match_dal.get_match_winners(match_id)
    data['participants'] = match_dal.get_match_participants(match_id)
    return data


@router.get('/{match_id}/participants')
def get_participants(match_id: int):
    return match_dal.get_match_participants(match_id)


@router.post('/{match_id}/result')
def submit_result(match_id: int, body: MatchResult):
    total = len(body.participants)
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            '''SELECT mc.criteria_id, mc.max_mm_diff,
                      mc.max_wait_time, mc.priority_type,
                      mc.mode_id, mc.engine_id
               FROM   MATCH m
               JOIN   MATCHMAKING_SESSION ms
                      ON  ms.session_id  = m.session_id
               JOIN   MATCHMAKING_CRITERIA mc
                      ON  mc.criteria_id = ms.criteria_id
               WHERE  m.match_id = :1''',
            [match_id])
        row = cur.fetchone()

    if not row:
        raise HTTPException(
            404,
            f'Match {match_id} not found or has no criteria linked')
    mc     = MatchmakingCriteria(*row)
    engine = load_engine_for_mode(mc.mode_id, mc)
    rating = engine.rating_engine
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            'SELECT AVG(mmr_before) FROM MATCH_PARTICIPANT WHERE match_id=:1',
            [match_id])
        lobby_avg = float(cur.fetchone()[0] or 1000)

    for p in body.participants:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                'SELECT mmr_before FROM MATCH_PARTICIPANT WHERE match_id=:1 AND player_id=:2',
                [match_id, p.player_id])
            prow = cur.fetchone()
        mmr_before = int(prow[0]) if prow else 1000
        delta = rating.compute_delta(
            player_mmr=mmr_before,
            opponent_avg_mmr=lobby_avg,
            won=bool(p.is_winner),
            placement=p.placement,
            total_players=total,
        )

        match_dal.update_participant_result(
            match_id=match_id,
            player_id=p.player_id,
            placement=p.placement,
            survival_time=p.survival_time,
            kills=p.kills,
            assists=p.assists,
            revives=p.revives,
            damage_done=p.damage_done,
            damage_taken=p.damage_taken,
            is_winner=p.is_winner,
            mmr_delta=delta,
            role_used=p.role_used,
        )
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
        row  = cur.fetchone()
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