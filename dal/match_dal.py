from db.connection import get_conn 
from models.entities import Match, Team, MatchParticipant 
 
def create_match(session_id, mode_id, region, match_mmr): 
    sql = '''INSERT INTO MATCH 
               (match_id,match_region,status,m_start_time,match_mmr,session_id,mode_id) 
             VALUES (seq_match.NEXTVAL,:1,'PENDING',SYSTIMESTAMP,:2,:3,:4) 
             RETURNING match_id INTO :5''' 
    with get_conn() as conn: 
        try: 
            cur = conn.cursor() 
            out = cur.var(int) 
            cur.execute(sql, [region, match_mmr, session_id, mode_id, out]) 
            conn.commit() 
            return get_match(out.getvalue()[0]) 
        except Exception: 
            conn.rollback(); raise 
 
def get_match(match_id): 
    with get_conn() as conn: 
        cur = conn.cursor() 
        cur.execute('SELECT * FROM MATCH WHERE match_id=:1', [match_id]) 
        row = cur.fetchone() 
    return Match(*row) if row else None 

def get_match_participants(match_id):
    sql = '''SELECT mp.player_id, p.username, mp.team_id 
             FROM MATCH_PARTICIPANT mp 
             JOIN PLAYER p ON p.player_id=mp.player_id 
             WHERE mp.match_id=:1'''
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(sql, [match_id])
        cols = [d[0].lower() for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]
 
def create_team(match_id, team_number, avg_team_mmr): 
    sql = '''INSERT INTO TEAM (team_id,match_id,team_number,avg_team_mmr) 
             VALUES (seq_team.NEXTVAL,:1,:2,:3) RETURNING team_id INTO :4''' 
    with get_conn() as conn: 
        try: 
            cur = conn.cursor() 
            out = cur.var(int) 
            cur.execute(sql, [match_id, team_number, avg_team_mmr, out]) 
            conn.commit() 
            return Team(out.getvalue()[0], match_id, team_number, avg_team_mmr) 
        except Exception: 
            conn.rollback(); raise 
    
def bulk_insert_participants(participants): 
    sql = '''INSERT INTO MATCH_PARTICIPANT 
               (player_id,match_id,team_id,role_used,placement,survival_time, 
                kills,assists,revives,damage_done,damage_taken,is_winner,mmr_before,mmr_delta) 
             VALUES (:1,:2,:3,:4,:5,:6,:7,:8,:9,:10,:11,:12,:13,:14)''' 
    data = [[p.player_id,p.match_id,p.team_id,p.role_used,p.placement, 
             p.survival_time,p.kills,p.assists,p.revives,p.damage_done, 
             p.damage_taken,p.is_winner,p.mmr_before,p.mmr_delta] 
            for p in participants] 
    with get_conn() as conn: 
        try: 
            conn.cursor().executemany(sql, data) 
            conn.commit() 
        except Exception: 
            conn.rollback(); raise 
 
def update_participant_result(match_id, player_id, placement, survival_time, 
                               kills, assists, revives, damage_done, damage_taken, 
                               is_winner, mmr_delta, role_used=None): 
    sql = '''UPDATE MATCH_PARTICIPANT 
             SET placement=:1,survival_time=:2,kills=:3,assists=:4,revives=:5, 
                 damage_done=:6,damage_taken=:7,is_winner=:8,mmr_delta=:9,role_used=:10 
             WHERE match_id=:11 AND player_id=:12''' 
    with get_conn() as conn: 
        try: 
            conn.cursor().execute(sql, [placement,survival_time,kills,assists,revives, 
                damage_done,damage_taken,is_winner,mmr_delta,role_used,match_id,player_id]) 
            conn.commit() 
        except Exception: 
            conn.rollback(); raise 
 
def finalise_match(match_id): 
    with get_conn() as conn: 
        try: 
            conn.cursor().execute( 
                "UPDATE MATCH SET status='COMPLETED',m_end_time=SYSTIMESTAMP WHERE match_id=:1", 
                [match_id]) 
            conn.commit() 
        except Exception: 
            conn.rollback(); raise 
def get_leaderboard(metric, mode_type, limit):
    valid_metrics = ['kills', 'assists', 'wins', 'damage_done']
    if metric not in valid_metrics:
        raise ValueError(f'Invalid metric: {metric}')
    
    agg = f'SUM(mp.{metric})' if metric != 'wins' else 'SUM(mp.is_winner)'
    
    sql = f"""
        SELECT p.username, {agg} as score
        FROM MATCH_PARTICIPANT mp
        JOIN MATCH m ON m.match_id = mp.match_id
        JOIN GAME_MODE gm ON gm.mode_id = m.mode_id
        JOIN PLAYER p ON p.player_id = mp.player_id
        WHERE gm.mode_type = :1
        GROUP BY p.username
        ORDER BY score DESC
        FETCH FIRST :2 ROWS ONLY
    """
    from db.connection import get_conn
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(sql, [mode_type, limit])
        return [{'username': r[0], 'score': r[1]} for r in cur.fetchall()]
