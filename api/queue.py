from fastapi import APIRouter, HTTPException 
from pydantic import BaseModel 
from dal import queue_dal, session_dal 
from engine.matchmaker import assemble_lobby 
from db.connection import get_conn 
from models.entities import GameMode, MatchmakingCriteria 
 
router = APIRouter() 
 
class EnqueueReq(BaseModel): 
    party_id: int 
    mode_id: int 
 
@router.post('/', status_code=202) 
def enqueue(body: EnqueueReq): 
    with get_conn() as conn: 
        cur = conn.cursor() 
        cur.execute('SELECT * FROM GAME_MODE WHERE mode_id=:1', [body.mode_id]) 
        row = cur.fetchone() 
    if not row: raise HTTPException(404, 'Game mode not found') 
    gm = GameMode(*row) 
    with get_conn() as conn: 
        cur = conn.cursor() 
        cur.execute('SELECT * FROM MATCHMAKING_CRITERIA WHERE mode_id=:1 AND ROWNUM=1', 
                    [body.mode_id]) 
        crow = cur.fetchone() 
    if not crow: raise HTTPException(500, 'No criteria configured for this mode') 
    mc = MatchmakingCriteria(*crow) 
    try: 
        entry = queue_dal.enqueue_party(body.party_id, body.mode_id, gm.mode_type) 
    except ValueError as e: 
        raise HTTPException(409, str(e)) 
    session = session_dal.create_session(mc.criteria_id) 
    match_id = assemble_lobby( 
        mode=gm, criteria=mc, session_id=session.session_id, region='AS-EAST') 
    if not match_id: 
        session_dal.fail_session(session.session_id) 
    return {'queue_no': entry.queue_no, 'match_id': match_id} 
 
@router.post('/expire-timeouts') 
def expire_timeouts(): 
    return {'expired': queue_dal.expire_stale()} 
 
@router.get('/waiting-monitor') 
def waiting_monitor(): 
    sql = '''SELECT q.queue_no, q.party_id, 
                    ROUND((SYSDATE-CAST(q.enqueue_time AS DATE))*86400) AS wait_secs, 
                    mc.max_wait_time, mc.max_mm_diff 
             FROM   QUEUE q 
             JOIN   GAME_MODE gm ON gm.mode_id=q.mode_id 
             JOIN   MATCHMAKING_CRITERIA mc ON mc.mode_id=gm.mode_id 
             WHERE  q.status='WAITING' 
             AND    (SYSDATE-CAST(q.enqueue_time AS DATE))*86400 > mc.max_wait_time 
             ORDER  BY wait_secs DESC''' 
    with get_conn() as conn: 
        cur = conn.cursor() 
        cur.execute(sql) 
        cols = [d[0].lower() for d in cur.description] 
        return [dict(zip(cols, r)) for r in cur.fetchall()] 
