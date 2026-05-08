import streamlit as st 
import requests 
import pandas as pd 
 
API = 'http://localhost:8000' 
 
st.set_page_config(page_title='Match Results', page_icon='🏆', layout='wide') 
st.markdown('# 🏆 Match Results') 
st.divider() 
 
tab1, tab2 = st.tabs(['Submit Result', 'View Match']) 
 
# ── Tab 1: Submit Result ───────────────────────────────────────── 
with tab1: 
    st.markdown('### Submit Post-Match Statistics') 
    st.caption('Game server submits this after a match ends. MMR is computed and updated automatically.') 
 
    match_id = st.number_input( 
        'Match ID', 
        min_value=1, step=1, 
        value=st.session_state.get('last_match_id', 1), 
    ) 
 
    n_players = st.number_input('Number of Players in Match', min_value=2, max_value=100, value=2, step=1) 
 
    participants = [] 
    st.markdown('---') 
    st.markdown('**Enter stats for each player:**') 
 
    role_map = {'fragger': 'fragger', 'tank': 'tank', 'support': 'support', 
                'scout': 'scout', 'dps': 'dps', 'none': None} 
 
    for i in range(int(n_players)): 
        with st.expander(f'Player {i+1}', expanded=(i == 0)): 
            c1, c2, c3 = st.columns(3) 
            with c1: 
                p_id       = st.number_input('Player ID',    min_value=1, step=1, key=f'pid_{i}') 
                placement  = st.number_input('Placement',    min_value=1, step=1, key=f'place_{i}') 
                is_winner  = st.selectbox('Winner?', [0, 1], key=f'win_{i}', 
                                          format_func=lambda x: 'Yes' if x == 1 else 'No') 
            with c2: 
                kills      = st.number_input('Kills',        min_value=0, step=1, key=f'kills_{i}') 
                assists    = st.number_input('Assists',       min_value=0, step=1, key=f'ast_{i}') 
                revives    = st.number_input('Revives',       min_value=0, step=1, key=f'rev_{i}') 
            with c3: 
                dmg_done   = st.number_input('Damage Done',  min_value=0, step=100, key=f'dd_{i}') 
                dmg_taken  = st.number_input('Damage Taken', min_value=0, step=100, key=f'dt_{i}') 
                surv       = st.number_input('Survival (s)', min_value=0, step=10,  key=f'surv_{i}') 
                role_used  = st.selectbox('Role Used', list(role_map.keys()), key=f'role_{i}') 
            participants.append({ 
                'player_id': p_id, 'placement': placement, 'is_winner': is_winner, 
                'kills': kills, 'assists': assists, 'revives': revives, 
                'damage_done': dmg_done, 'damage_taken': dmg_taken, 
                'survival_time': surv, 'role_used': role_map[role_used], 
            }) 
 
    if st.button('Submit Match Result', type='primary', use_container_width=True): 
        r = requests.post(f'{API}/matches/{match_id}/result', 
                          json={'participants': participants}) 
        if r.status_code == 200: 
            st.success('Match finalised! MMR updated for all players.') 
            st.json(r.json()) 
        else: 
            st.error(f'Error {r.status_code}: {r.text}') 

# ── Tab 2: View Match ──────────────────────────────────────────── 
with tab2: 
    st.markdown('### View Match Details') 
    vm_id = st.number_input('Match ID', min_value=1, step=1, key='vm_id') 
    col1, col2 = st.columns(2) 
 
    with col1: 
        if st.button('Load Match Info', use_container_width=True): 
            r = requests.get(f'{API}/matches/{vm_id}') 
            if r.status_code == 200: 
                data = r.json() 
                st.markdown(f"**Mode:** {data.get('mode_name', 'Unknown')}")
                
                # Split metrics into columns to save vertical space
                m1, m2 = st.columns(2)
                with m1:
                    st.markdown(f"**Region:** {data['match_region']}")
                    st.markdown(f"**Match MMR:** {data['match_mmr']}")
                    st.markdown(f"**Session ID:** {data['session_id']}")
                with m2:
                    st.markdown(f"**Status:** {data['status']}")
                    # Format datetimes nicely if they exist
                    start_t = data.get('m_start_time')
                    end_t = data.get('m_end_time')
                    st.markdown(f"**Start Time:** {start_t[:19].replace('T', ' ') if start_t else 'N/A'}")
                    st.markdown(f"**End Time:** {end_t[:19].replace('T', ' ') if end_t else 'N/A'}")

                # ── Winner display ────────────────────────────
                winner_info = data.get('winner_info', {})
                winner_type = winner_info.get('winner_type')
                winners = winner_info.get('winners', [])

                if winner_type and winners:
                    st.markdown('---')
                    st.markdown('#### 🏆 Winner')
                    if winner_type == 'player':
                        for w in winners:
                            st.success(f"**Player:** {w['username']}  (ID: {w['player_id']})")
                    elif winner_type == 'team':
                        for w in winners:
                            members = ', '.join(
                                f"{m['username']} (ID: {m['player_id']})"
                                for m in w.get('members', [])
                            )
                            st.success(
                                f"**Winning Team** (ID: {w['team_id']})  \n"
                                f"**Members:** {members}"
                            )
                    elif winner_type == 'party':
                        for w in winners:
                            members = ', '.join(
                                f"{m['username']} (ID: {m['player_id']})"
                                for m in w.get('members', [])
                            )
                            st.success(
                                f"**Party ID:** {w['party_id']}  "
                                f"({w.get('party_type', 'team')})  \n"
                                f"**Members:** {members}"
                            )
                elif data['status'] == 'COMPLETED':
                    st.info('No winner recorded for this match.')

                # ── Participants table ────────────────────────
                participants = data.get('participants', [])
                if participants:
                    st.markdown('---')
                    st.markdown('#### 👥 Participants')
                    df = pd.DataFrame(participants)
                    display_cols = [c for c in ['player_id', 'username', 'team_id',
                                                'placement', 'kills', 'assists',
                                                'damage_done', 'is_winner',
                                                'mmr_before', 'mmr_delta'] if c in df.columns]
                    st.dataframe(df[display_cols], use_container_width=True, hide_index=True)
            else: 
                st.warning('Match not found') 
 
    with col2: 
        if st.button('Lobby Quality Report', use_container_width=True): 
            r = requests.get(f'{API}/matches/{vm_id}/lobby-quality') 
            if r.status_code == 200: 
                data = r.json() 
                if data: 
                    st.metric('Lobby Avg MMR', data.get('lobby_avg_mmr', 'N/A')) 
                    st.metric('MMR Std Dev', data.get('mmr_std_dev', 'N/A'), 
                              help='Lower = fairer lobby') 
                    st.metric('MMR Spread', data.get('mmr_spread', 'N/A')) 
                    st.json(data) 
                else: 
                    st.info('No team data for this match') 
            else: 
                st.error(f'Error: {r.text}')