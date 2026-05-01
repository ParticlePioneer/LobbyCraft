import uuid
import random
import sys
import db.connection as db
from dal import player_dal, party_dal, queue_dal, session_dal, match_dal
from engine.matchmaker import assemble_lobby
from models.entities import GameMode, MatchmakingCriteria

db.init_pool()

def get_uniq_user(prefix="u"):
    return f"{prefix}_{uuid.uuid4().hex[:6]}"

print("Creating 20 players...")
players = []
for i in range(20):
    p = player_dal.create_player(get_uniq_user('pro'), 'AS-EAST')
    players.append(p)

print("Forming 2 squad parties of 5...")
parties = []
for i in range(2):
    # a team needs 5 players
    team_pids = [players[i*5 + j].player_id for j in range(5)]
    party = party_dal.create_party('squad', team_pids)
    parties.append(party)

print("Enqueuing parties for Ranked 5v5 (mode_id=4)...")
mode_id = 4
for party in parties:
    queue_dal.enqueue_party(party.party_id, mode_id, 'competitive_5v5')

print("Assembling lobby...")
# Mock session criteria
with db.get_conn() as conn:
    cur = conn.cursor()
    cur.execute('SELECT * FROM GAME_MODE WHERE mode_id=:1', [mode_id])
    gm = GameMode(*cur.fetchone())
    cur.execute('SELECT * FROM MATCHMAKING_CRITERIA WHERE mode_id=:1 AND ROWNUM=1', [mode_id])
    mc = MatchmakingCriteria(*cur.fetchone())

session = session_dal.create_session(mc.criteria_id)
match_id = assemble_lobby(gm, mc, session.session_id, 'AS-EAST')

if not match_id:
    print("Failed to assemble lobby!")
    session_dal.fail_session(session.session_id)
    sys.exit(1)

print(f"Match {match_id} assembled successfully!")

print("Generating random results for match...")
participants = match_dal.get_match_participants(match_id)
for idx, p in enumerate(participants):
    is_winner = 1 if p['team_id'] == participants[0]['team_id'] else 0
    delta = 25 if is_winner else -15
    match_dal.update_participant_result(
        match_id=match_id, player_id=p['player_id'],
        placement=1 if is_winner else random.randint(2, 5),
        survival_time=random.randint(600, 1800),
        kills=random.randint(1, 10), assists=random.randint(0, 8),
        revives=random.randint(0, 3), damage_done=random.randint(1000, 4000),
        damage_taken=random.randint(500, 3000), is_winner=is_winner,
        mmr_delta=delta, role_used='Flex'
    )
    player_dal.update_mmr(p['player_id'], delta)

match_dal.finalise_match(match_id)

print(f"Seed complete! Data populated for Match ID {match_id}. You can now view Analytics.")
