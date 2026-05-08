from db.connection import get_conn


def get_all_engines():
    """Return all matchmaking engines."""
    sql = '''SELECT engine_id, engine_name, engine_class, is_active
             FROM   MATCHMAKING_ENGINE
             ORDER  BY engine_id'''
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(sql)
        cols = [d[0].lower() for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]


def get_engine_params(engine_id):
    """Return all parameters for a specific engine."""
    sql = '''SELECT param_id, param_key, param_value, param_type
             FROM   ENGINE_PARAMETER
             WHERE  engine_id = :1
             ORDER  BY param_key'''
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(sql, [engine_id])
        cols = [d[0].lower() for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]


def get_modes_with_engine():
    """
    Return all game modes joined with their criteria and assigned engine.
    Each mode shows its criteria_id, engine_id, and engine_name.
    """
    sql = '''SELECT gm.mode_id, gm.mode_name, gm.mode_type,
                    gm.team_size, gm.max_players,
                    mc.criteria_id, mc.max_mm_diff, mc.max_wait_time,
                    mc.engine_id,
                    NVL(me.engine_name, 'Not Assigned') AS engine_name
             FROM   GAME_MODE gm
             JOIN   MATCHMAKING_CRITERIA mc ON mc.mode_id = gm.mode_id
             LEFT   JOIN MATCHMAKING_ENGINE me ON me.engine_id = mc.engine_id
             ORDER  BY gm.mode_id'''
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(sql)
        cols = [d[0].lower() for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]


def update_mode_engine(criteria_id, engine_id):
    """Update the engine_id on a MATCHMAKING_CRITERIA row."""
    sql = '''UPDATE MATCHMAKING_CRITERIA
             SET    engine_id = :1
             WHERE  criteria_id = :2'''
    with get_conn() as conn:
        try:
            cur = conn.cursor()
            cur.execute(sql, [engine_id, criteria_id])
            n = cur.rowcount
            conn.commit()
            return n
        except Exception:
            conn.rollback(); raise


def get_lobby_quality_batch(mode_id=None, engine_id=None, limit=50):
    """
    Fetch lobby quality metrics for recent matches, optionally filtered
    by mode and/or engine.  Joins through:
        MATCH → MATCHMAKING_SESSION → MATCHMAKING_CRITERIA → MATCHMAKING_ENGINE
    and aggregates TEAM stats per match.
    """
    conditions = []
    params = {}

    if mode_id is not None:
        conditions.append('m.mode_id = :mode_id')
        params['mode_id'] = mode_id
    if engine_id is not None:
        conditions.append('mc.engine_id = :engine_id')
        params['engine_id'] = engine_id

    where = ('WHERE ' + ' AND '.join(conditions)) if conditions else ''
    params['lim'] = limit

    sql = f'''
        SELECT m.match_id,
               m.m_start_time,
               m.match_mmr,
               m.mode_id,
               gm.mode_name,
               mc.engine_id,
               NVL(me.engine_name, 'Unknown') AS engine_name,
               COUNT(t.team_id)                         AS team_count,
               ROUND(AVG(t.avg_team_mmr), 2)            AS lobby_avg_mmr,
               ROUND(STDDEV(t.avg_team_mmr), 2)         AS mmr_std_dev,
               MAX(t.avg_team_mmr) - MIN(t.avg_team_mmr) AS mmr_spread
        FROM   MATCH m
        JOIN   TEAM t                  ON t.match_id   = m.match_id
        JOIN   GAME_MODE gm            ON gm.mode_id   = m.mode_id
        JOIN   MATCHMAKING_SESSION ms  ON ms.session_id = m.session_id
        JOIN   MATCHMAKING_CRITERIA mc ON mc.criteria_id = ms.criteria_id
        LEFT   JOIN MATCHMAKING_ENGINE me ON me.engine_id = mc.engine_id
        {where}
        GROUP  BY m.match_id, m.m_start_time, m.match_mmr, m.mode_id,
                  gm.mode_name, mc.engine_id, me.engine_name
        ORDER  BY m.m_start_time DESC
        FETCH  FIRST :lim ROWS ONLY
    '''
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        cols = [d[0].lower() for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]
