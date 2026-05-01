import random
import sys
from datetime import datetime, timedelta
import db.connection as db
from dal import player_dal, match_dal, session_dal

# Initialize database
db.init_pool()

def get_game_modes():
    with db.get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT mode_id, team_size, max_players, mode_type FROM GAME_MODE")
        return cur.fetchall()

def get_criteria_mapping():
    with db.get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT mode_id, criteria_id FROM MATCHMAKING_CRITERIA")
        return dict(cur.fetchall())

def create_more_players(count=200):
    current_count = 0
    with db.get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM PLAYER")
        current_count = cur.fetchone()[0]
    
    needed = max(0, count - current_count)
    if needed > 0:
        print(f"Creating {needed} additional players...")
        for i in range(needed):
            username = f"player_{current_count + i}_{random.randint(1000, 9999)}"
            player_dal.create_player(username, random.choice(['AS-EAST', 'US-WEST', 'EU-CENTRAL']))
    
    with db.get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT player_id, current_mmr FROM PLAYER")
        return cur.fetchall()

def seed_massive(match_count=500):
    modes = get_game_modes()
    criteria_map = get_criteria_mapping()
    players = create_more_players(300) 
    
    print(f"Starting to seed {match_count} matches...")
    
    with db.get_conn() as conn:
        for i in range(match_count):
            mode = random.choice(modes)
            mode_id, team_size, max_players, mode_type = mode
            criteria_id = criteria_map.get(mode_id)
            
            if not criteria_id:
                continue
                
            cur = conn.cursor()
            
            # 1. Create Session
            sid_var = cur.var(int)
            cur.execute("INSERT INTO MATCHMAKING_SESSION (session_id, status, criteria_id) VALUES (seq_mm_session.NEXTVAL, 'COMPLETED', :1) RETURNING session_id INTO :2", [criteria_id, sid_var])
            session_id = sid_var.getvalue()[0]
            
            # 2. Create Match
            region = random.choice(['AS-EAST', 'US-WEST', 'EU-CENTRAL'])
            match_mmr = random.randint(800, 2500)
            start_time = datetime.now() - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
            
            mid_var = cur.var(int)
            sql = '''INSERT INTO MATCH 
                       (match_id,match_region,status,m_start_time,match_mmr,session_id,mode_id) 
                     VALUES (seq_match.NEXTVAL,:1,'COMPLETED',:2,:3,:4,:5) 
                     RETURNING match_id INTO :6'''
            cur.execute(sql, [region, start_time, match_mmr, session_id, mode_id, mid_var])
            match_id = mid_var.getvalue()[0]
            
            # 3. Create Teams and Participants
            num_teams = max_players // team_size
            match_players = random.sample(players, max_players)
            winner_team_idx = random.randint(0, num_teams - 1)
            
            participants_data = []
            
            for t_idx in range(num_teams):
                team_players = match_players[t_idx * team_size : (t_idx + 1) * team_size]
                avg_mmr = sum(p[1] for p in team_players) // team_size
                
                tid_var = cur.var(int)
                cur.execute("INSERT INTO TEAM (team_id,match_id,team_number,avg_team_mmr) VALUES (seq_team.NEXTVAL,:1,:2,:3) RETURNING team_id INTO :4", [match_id, t_idx+1, avg_mmr, tid_var])
                team_id = tid_var.getvalue()[0]
                
                is_winner_team = (t_idx == winner_team_idx)
                
                for p_id, p_mmr in team_players:
                    kills = random.randint(0, 15) if mode_type == 'battle_royale' else random.randint(0, 30)
                    assists = random.randint(0, 10)
                    revives = random.randint(0, 5)
                    damage = random.randint(500, 5000)
                    placement = 1 if is_winner_team else random.randint(2, num_teams)
                    is_winner = 1 if is_winner_team else 0
                    mmr_delta = random.randint(15, 30) if is_winner else random.randint(-25, -10)
                    
                    # Batch participant data
                    participants_data.append([p_id, match_id, team_id, 'Random', placement, 
                                            random.randint(300, 1800), kills, assists, revives, 
                                            damage, random.randint(500, 4000), is_winner, p_mmr, mmr_delta])
                    
                    # Update MMR
                    cur.execute("UPDATE PLAYER SET current_mmr=GREATEST(0,current_mmr+:1) WHERE player_id=:2", [mmr_delta, p_id])

            # Bulk insert participants for this match
            sql_part = '''INSERT INTO MATCH_PARTICIPANT 
                           (player_id,match_id,team_id,role_used,placement,survival_time, 
                            kills,assists,revives,damage_done,damage_taken,is_winner,mmr_before,mmr_delta) 
                         VALUES (:1,:2,:3,:4,:5,:6,:7,:8,:9,:10,:11,:12,:13,:14)'''
            cur.executemany(sql_part, participants_data)
            
            # Finalize match
            cur.execute("UPDATE MATCH SET status='COMPLETED',m_end_time=SYSTIMESTAMP WHERE match_id=:1", [match_id])
            
            conn.commit()
            
            if (i + 1) % 10 == 0:
                print(f"Seeded {i + 1} matches...")

    print("Seeding completed successfully!")


if __name__ == "__main__":
    seed_massive(500)
