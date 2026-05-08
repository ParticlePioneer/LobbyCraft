from db.connection import get_conn 
from models.entities import Player 
 
def create_player(username, region, sys_role_id=1): 
    sql = '''INSERT INTO PLAYER (player_id,username,region,sys_role_id) 
             VALUES (seq_player.NEXTVAL,:1,:2,:3) RETURNING player_id INTO :4''' 
    with get_conn() as conn: 
        try: 
            cur = conn.cursor() 
            out = cur.var(int) 
            cur.execute(sql, [username, region, sys_role_id, out]) 
            conn.commit() 
            return get_player(out.getvalue()[0]) 
        except Exception: 
            conn.rollback(); raise 
 
def get_player(player_id): 
    with get_conn() as conn: 
        cur = conn.cursor() 
        cur.execute('SELECT * FROM PLAYER WHERE player_id=:1', [player_id]) 
        row = cur.fetchone() 
    return Player(*row) if row else None 
 
def update_mmr(player_id, delta): 
    with get_conn() as conn: 
        try: 
            conn.cursor().execute( 
                'UPDATE PLAYER SET current_mmr=GREATEST(0,current_mmr+:1) WHERE player_id=:2', 
                [delta, player_id]) 
            conn.commit() 
        except Exception: 
            conn.rollback(); raise 
 
def get_mmr_history(player_id): 
    sql = '''SELECT mp.match_id, m.m_start_time, mp.mmr_before, 
                    mp.mmr_delta, mp.mmr_before+mp.mmr_delta AS mmr_after 
             FROM   MATCH_PARTICIPANT mp 
             JOIN   MATCH m ON m.match_id=mp.match_id 
             WHERE  mp.player_id=:1 ORDER BY m.m_start_time ASC''' 
    with get_conn() as conn: 
        cur = conn.cursor() 
        cur.execute(sql, [player_id]) 
        cols = [d[0].lower() for d in cur.description] 
        return [dict(zip(cols, r)) for r in cur.fetchall()] 
 
def set_role_preference(player_id, role_id, priority): 
    sql = '''MERGE INTO ROLE_PREFERENCE rp USING DUAL 
             ON (rp.player_id=:pid AND rp.role_id=:rid) 
             WHEN MATCHED THEN UPDATE SET rp.priority=:pri 
             WHEN NOT MATCHED THEN INSERT (player_id,role_id,priority) VALUES (:pid,:rid,:pri)''' 
    with get_conn() as conn: 
        try: 
            conn.cursor().execute(sql, {'pid': player_id, 'rid': role_id, 'pri': priority}) 
            conn.commit()
        except Exception: 
            conn.rollback(); raise 