from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dal import queue_dal, session_dal
from engine.loader import load_engine_for_mode
from engine.matchmaker import assemble_lobby
from db.connection import get_conn
from models.entities import GameMode, MatchmakingCriteria

router = APIRouter()


class EnqueueReq(BaseModel):
    party_id: int
    mode_id:  int


@router.post('/', status_code=202)
def enqueue(body: EnqueueReq):

    # Fetch game mode
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            'SELECT * FROM GAME_MODE WHERE mode_id = :1',
            [body.mode_id])
        row = cur.fetchone()
    if not row:
        raise HTTPException(404, 'Game mode not found')
    gm = GameMode(*row)

    # Fetch criteria for this mode
    # SELECT * now returns engine_id as the last column
    # because we ran ALTER TABLE in engine_seed.sql
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            '''SELECT criteria_id, max_mm_diff, max_wait_time,
                      priority_type, mode_id, engine_id
               FROM   MATCHMAKING_CRITERIA
               WHERE  mode_id = :1
               AND    ROWNUM  = 1''',
            [body.mode_id])
        crow = cur.fetchone()
    if not crow:
        raise HTTPException(
            500, 'No criteria configured for this mode')
    mc = MatchmakingCriteria(*crow)

    # Guard: reject if party already waiting in this mode
    try:
        entry = queue_dal.enqueue_party(
            body.party_id, body.mode_id, gm.mode_type)
    except ValueError as e:
        raise HTTPException(409, str(e))

    # Create matchmaking session
    session = session_dal.create_session(mc.criteria_id)

    # Load whichever engine is configured for this mode's criteria.
    # This is the only line that replaced the old hardwired MMREngine.
    try:
        engine = load_engine_for_mode(gm.mode_id, mc)
    except ValueError as e:
        session_dal.fail_session(session.session_id)
        raise HTTPException(500, str(e))

    # Attempt lobby assembly using the loaded engine
    match_id = assemble_lobby(
        engine=engine,
        mode=gm,
        session_id=session.session_id,
        region='AS-EAST',
    )

    if not match_id:
        session_dal.fail_session(session.session_id)

    return {'queue_no': entry.queue_no, 'match_id': match_id}


@router.post('/expire-timeouts')
def expire_timeouts():
    return {'expired': queue_dal.expire_stale()}


@router.get('/waiting-monitor')
def waiting_monitor():
    """
    Returns queue entries that have exceeded their wait time limit.
    Now also returns engine_name so you can see which engine
    each overdue entry is waiting on.
    """
    sql = '''
        SELECT q.queue_no,
               q.party_id,
               ROUND((SYSDATE - CAST(q.enqueue_time AS DATE))
                     * 86400)         AS wait_secs,
               mc.max_wait_time,
               mc.max_mm_diff,
               me.engine_name
        FROM   QUEUE q
        JOIN   GAME_MODE gm
               ON  gm.mode_id  = q.mode_id
        JOIN   MATCHMAKING_CRITERIA mc
               ON  mc.mode_id  = gm.mode_id
        JOIN   MATCHMAKING_ENGINE me
               ON  me.engine_id = mc.engine_id
        WHERE  q.status = 'WAITING'
        AND    (SYSDATE - CAST(q.enqueue_time AS DATE)) * 86400
               > mc.max_wait_time
        ORDER  BY wait_secs DESC
    '''
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(sql)
        cols = [d[0].lower() for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]