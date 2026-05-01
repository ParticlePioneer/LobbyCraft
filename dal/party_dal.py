from db.connection import get_conn 
from models.entities import Party, PartyMember 
 
def create_party(party_type, player_ids): 
    with get_conn() as conn: 
        try: 
            cur = conn.cursor() 
            out = cur.var(int) 
            cur.execute( 
                'INSERT INTO PARTY (party_id,party_type) VALUES (seq_party.NEXTVAL,:1) RETURNING party_id INTO :2', 
                [party_type, out]) 
            pid = out.getvalue()[0] 
            cur.executemany( 
                'INSERT INTO PARTY_MEMBER (party_id,player_id) VALUES (:1,:2)', 
                [(pid, p) for p in player_ids]) 
            conn.commit() 
            return get_party(pid) 
        except Exception: 
            conn.rollback(); raise 
 
def get_party(party_id): 
    with get_conn() as conn: 
        cur = conn.cursor() 
        cur.execute('SELECT * FROM PARTY WHERE party_id=:1', [party_id]) 
        row = cur.fetchone() 
    return Party(*row) if row else None 
 
def get_party_members(party_id): 
    with get_conn() as conn: 
        cur = conn.cursor() 
        cur.execute('SELECT * FROM PARTY_MEMBER WHERE party_id=:1', [party_id]) 
        return [PartyMember(*r) for r in cur.fetchall()]