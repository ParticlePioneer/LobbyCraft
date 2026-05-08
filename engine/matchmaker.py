from dal import match_dal, queue_dal, session_dal
from dal.player_dal import get_player
from db.connection import get_conn
from models.entities import MatchParticipant


def assemble_lobby(engine, mode, session_id: int,
                   region: str):
    """
    Generic lobby assembly orchestrator.
    Works with any engine that implements BaseMatchmakingEngine.
    Contains zero algorithm logic — delegates everything to engine.

    Steps:
      1. Ask the engine for eligible candidates from QUEUE.
      2. Ask the engine to select parties and form LobbyTeam objects.
      3. Write MATCH record to DB.
      4. Write TEAM records to DB.
      5. Write placeholder MATCH_PARTICIPANT rows to DB.
      6. Mark all selected QUEUE entries as MATCHED.
      7. Mark the MATCHMAKING_SESSION as COMPLETED.

    Args:
        engine     : any BaseMatchmakingEngine instance
        mode       : GameMode dataclass instance
        session_id : ID of the current MATCHMAKING_SESSION row
        region     : match region string (e.g. 'AS-EAST')

    Returns:
        match_id (int) if lobby assembled successfully.
        None if not enough players in queue.
    """

    # ── Step 1: Engine fetches eligible candidates ────────────────
    candidates = engine.get_candidates(mode.mode_id, region)

    # ── Step 2: Engine selects parties and forms teams ────────────
    teams = engine.select_and_form_teams(candidates, mode)
    if teams is None:
        # Not enough players — caller will mark session as FAILED
        return None

    # ── Step 3: Compute lobby MMR and write MATCH row ─────────────
    lobby_mmr = engine.compute_lobby_mmr(teams)
    match = match_dal.create_match(
        session_id=session_id,
        mode_id=mode.mode_id,
        region=region,
        match_mmr=lobby_mmr,
    )

    # ── Step 4 & 5: Write TEAM and MATCH_PARTICIPANT rows ─────────
    # Batch: create all teams in one connection
    team_sql = '''INSERT INTO TEAM (team_id,match_id,team_number,avg_team_mmr)
                  VALUES (seq_team.NEXTVAL,:1,:2,:3) RETURNING team_id INTO :4'''
    team_ids = {}
    with get_conn() as conn:
        try:
            cur = conn.cursor()
            for team in teams:
                out = cur.var(int)
                cur.execute(team_sql, [match.match_id, team.team_number,
                                       team.avg_team_mmr, out])
                team_ids[team.team_number] = out.getvalue()[0]
            conn.commit()
        except Exception:
            conn.rollback(); raise

    # Batch: fetch all player MMRs in one connection
    all_pids = []
    for team in teams:
        all_pids.extend(team.player_ids)
    player_mmrs = {}
    if all_pids:
        ph = ','.join([f':{i+1}' for i in range(len(all_pids))])
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                f'SELECT player_id, current_mmr FROM PLAYER WHERE player_id IN ({ph})',
                all_pids)
            for pid, mmr in cur.fetchall():
                player_mmrs[pid] = mmr

    participants = []
    for team in teams:
        tid = team_ids[team.team_number]
        for pid in team.player_ids:
            participants.append(MatchParticipant(
                player_id=pid,
                match_id=match.match_id,
                team_id=tid,
                placement=0,
                survival_time=0,
                kills=0,
                assists=0,
                revives=0,
                damage_done=0,
                damage_taken=0,
                is_winner=0,
                mmr_before=player_mmrs.get(pid, 1000),
                mmr_delta=0,
            ))

    match_dal.bulk_insert_participants(participants)

    # ── Step 6: Mark queue entries as MATCHED ────────────────────
    queue_dal.mark_matched([t.queue_no for t in teams])

    # ── Step 7: Complete the session ─────────────────────────────
    session_dal.complete_session(session_id)

    return match.match_id