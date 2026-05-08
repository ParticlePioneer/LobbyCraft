from db.connection import get_conn 
from models.entities import QueueEntry, PartyWithMMR 
 
def enqueue_party(party_id, mode_id, queue_type): 
    with get_conn() as conn: 
        cur = conn.cursor() 
        cur.execute( 
            "SELECT COUNT(*) FROM QUEUE WHERE party_id=:1 AND mode_id=:2 AND status='WAITING'", 
            [party_id, mode_id]) 
        if cur.fetchone()[0] > 0: 
            raise ValueError('Party already WAITING in this mode') 
    sql = '''INSERT INTO QUEUE (queue_no,queue_type,party_id,mode_id) 
             VALUES (seq_queue.NEXTVAL,:1,:2,:3) RETURNING queue_no INTO :4''' 
    with get_conn() as conn: 
        try: 
            cur = conn.cursor() 
            out = cur.var(int) 
            cur.execute(sql, [queue_type, party_id, mode_id, out]) 
            conn.commit() 
            return get_queue_entry(out.getvalue()[0]) 
        except Exception: 
            conn.rollback(); raise 
 
def get_queue_entry(queue_no): 
    with get_conn() as conn: 
         cur = conn.cursor() 
         cur.execute('SELECT * FROM QUEUE WHERE queue_no=:1', [queue_no]) 
         row = cur.fetchone() 
    return QueueEntry(*row) if row else None 

def get_waiting_parties(mode_id, seed_mmr, max_diff): 
    sql = ''' 
        SELECT q.queue_no, q.party_id, q.enqueue_time, 
               AVG(p.current_mmr) AS avg_mmr, 
               LISTAGG(p.player_id,',') WITHIN GROUP (ORDER BY p.player_id) AS pids 
        FROM   QUEUE q 
        JOIN   PARTY_MEMBER pm ON pm.party_id=q.party_id 
        JOIN   PLAYER p        ON p.player_id=pm.player_id 
        WHERE  q.status='WAITING' AND q.mode_id=:1 
        GROUP  BY q.queue_no, q.party_id, q.enqueue_time 
        HAVING ABS(AVG(p.current_mmr)-:2) <= :3 
        ORDER  BY q.enqueue_time ASC''' 
    with get_conn() as conn: 
        cur = conn.cursor() 
        cur.execute(sql, [mode_id, seed_mmr, max_diff]) 
        rows = cur.fetchall() 
    result = [] 
    for qno, paid, et, avg_mmr, pids_str in rows: 
        result.append(PartyWithMMR( 
            queue_no=qno, party_id=paid, 
            player_ids=[int(x) for x in str(pids_str).split(',')], 
            avg_mmr=float(avg_mmr), enqueue_time=et)) 
    return result 
 
def mark_matched(queue_nos): 
    if not queue_nos: return 
    ph = ','.join([f':{i+1}' for i in range(len(queue_nos))]) 
    with get_conn() as conn: 
        try: 
            conn.cursor().execute( 
                f"UPDATE QUEUE SET status='MATCHED' WHERE queue_no IN ({ph})", queue_nos) 
            conn.commit() 
        except Exception: 
            conn.rollback(); raise 

def get_waiting_parties_all(mode_id):
    """Fetch ALL waiting parties for a mode (no MMR filter). Used by BucketEngine."""
    sql = '''
        SELECT q.queue_no, q.party_id, q.enqueue_time,
               AVG(p.current_mmr) AS avg_mmr,
               LISTAGG(p.player_id,',') WITHIN GROUP (ORDER BY p.player_id) AS pids
        FROM   QUEUE q
        JOIN   PARTY_MEMBER pm ON pm.party_id=q.party_id
        JOIN   PLAYER p        ON p.player_id=pm.player_id
        WHERE  q.status='WAITING' AND q.mode_id=:1
        GROUP  BY q.queue_no, q.party_id, q.enqueue_time
        ORDER  BY q.enqueue_time ASC'''
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(sql, [mode_id])
        rows = cur.fetchall()
    result = []
    for qno, paid, et, avg_mmr, pids_str in rows:
        result.append(PartyWithMMR(
            queue_no=qno, party_id=paid,
            player_ids=[int(x) for x in str(pids_str).split(',')],
            avg_mmr=float(avg_mmr), enqueue_time=et))
    return result
 
def expire_stale(): 
    sql = '''UPDATE QUEUE q SET q.status='EXPIRED' 
             WHERE q.status='WAITING' 
             AND (SYSDATE-CAST(q.enqueue_time AS DATE))*86400 > ( 
                 SELECT mc.max_wait_time FROM MATCHMAKING_CRITERIA mc 
                 WHERE mc.mode_id=q.mode_id AND ROWNUM=1)''' 
    with get_conn() as conn: 
        try: 
            cur = conn.cursor() 
            cur.execute(sql) 
            n = cur.rowcount 
            conn.commit() 
            return n 
        except Exception: 
            conn.rollback(); raise