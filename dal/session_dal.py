from db.connection import get_conn 
from models.entities import MatchmakingSession 
 
def create_session(criteria_id): 
    sql = '''INSERT INTO MATCHMAKING_SESSION (session_id,status,criteria_id) 
             VALUES (seq_mm_session.NEXTVAL,'SEARCHING',:1) RETURNING session_id INTO :2''' 
    with get_conn() as conn: 
        try: 
            cur = conn.cursor() 
            out = cur.var(int) 
            cur.execute(sql, [criteria_id, out]) 
            conn.commit() 
            return get_session(out.getvalue()[0]) 
        except Exception: 
            conn.rollback(); raise 

def get_session(session_id): 
    with get_conn() as conn: 
        cur = conn.cursor() 
        cur.execute('SELECT * FROM MATCHMAKING_SESSION WHERE session_id=:1', [session_id]) 
        row = cur.fetchone() 
    return MatchmakingSession(*row) if row else None 
 
def complete_session(session_id): 
    _set_status(session_id, 'COMPLETED') 
 
def fail_session(session_id): 
    _set_status(session_id, 'FAILED') 
 
def _set_status(session_id, status): 
    with get_conn() as conn: 
        try: 
            conn.cursor().execute( 
                'UPDATE MATCHMAKING_SESSION SET status=:1,end_time=SYSTIMESTAMP WHERE session_id=:2', 
                [status, session_id]) 
            conn.commit() 
        except Exception: 
            conn.rollback(); raise 