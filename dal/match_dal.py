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
    sql = '''SELECT mp.player_id, p.username, mp.team_id,
                    mp.is_winner, mp.kills, mp.assists, mp.damage_done,
                    mp.placement, mp.mmr_before, mp.mmr_delta
             FROM MATCH_PARTICIPANT mp
             JOIN PLAYER p ON p.player_id=mp.player_id
             WHERE mp.match_id=:1
             ORDER BY mp.placement'''
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(sql, [match_id])
        cols = [d[0].lower() for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]

def get_match_winners(match_id):
    """Return winner info for a match.
    - 1 winner (BR solo)         -> winner_type='player'
    - Team win, solo-queued      -> winner_type='team'   (team_id + members)
    - Team win, party-queued     -> winner_type='party'  (party_id + members)
    """
    sql = '''SELECT mp.player_id, p.username, mp.team_id, t.team_number,
                    pa.party_id, pa.party_type, gm.team_size, gm.mode_type
             FROM   MATCH_PARTICIPANT mp
             JOIN   PLAYER p  ON p.player_id  = mp.player_id
             JOIN   TEAM   t  ON t.team_id    = mp.team_id
             JOIN   MATCH  m  ON m.match_id   = mp.match_id
             JOIN   GAME_MODE gm ON gm.mode_id = m.mode_id
             LEFT JOIN PARTY_MEMBER pm ON pm.player_id = mp.player_id
             LEFT JOIN PARTY pa        ON pa.party_id  = pm.party_id
             WHERE  mp.match_id  = :1
               AND  mp.is_winner = 1'''
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(sql, [match_id])
        cols = [d[0].lower() for d in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]

    if not rows:
        return {'winner_type': None, 'winners': []}

    mode_type = rows[0].get('mode_type', 'battle_royale')

    # Only 1 winner → individual player (BR solo)
    if len(rows) == 1:
        r = rows[0]
        return {
            'winner_type': 'player',
            'mode_type': mode_type,
            'winners': [{'player_id': r['player_id'],
                         'username': r['username']}]
        }

    # Multiple winners → group by team_id
    # Check if any winner has a non-solo party (duo/squad)
    has_party = any(r.get('party_type') in ('duo', 'squad') for r in rows)

    if has_party:
        # Group by party_id for duo/squad winners
        seen_parties = {}
        for r in rows:
            pid = r.get('party_id')
            pt  = r.get('party_type')
            if pid and pt in ('duo', 'squad'):
                if pid not in seen_parties:
                    seen_parties[pid] = {
                        'party_id': pid,
                        'party_type': pt,
                        'members': []
                    }
                seen_parties[pid]['members'].append({
                    'player_id': r['player_id'],
                    'username': r['username']
                })
        return {
            'winner_type': 'party',
            'mode_type': mode_type,
            'winners': list(seen_parties.values())
        }
    else:
        # All solo-queued → show as team win with team_id
        team_id = rows[0].get('team_id')
        members = [{'player_id': r['player_id'],
                     'username': r['username']} for r in rows]
        return {
            'winner_type': 'team',
            'mode_type': mode_type,
            'winners': [{'team_id': team_id,
                         'members': members}]
        }
 
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
