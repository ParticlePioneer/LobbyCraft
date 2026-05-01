import streamlit as st 
import requests 
import pandas as pd 
 
API = 'http://localhost:8000' 
 
st.set_page_config(page_title='Parties & Queue', page_icon='🎯', layout='wide') 
st.markdown('# 🎯 Parties & Matchmaking Queue') 
st.divider() 
 
tab1, tab2, tab3 = st.tabs(['Create Party', 'Enter Queue', 'Queue Monitor']) 
 
# ── Tab 1: Create Party ────────────────────────────────────────── 
with tab1: 
    st.markdown('### Form a Party') 
    col1, col2 = st.columns(2) 
    with col1: 
        party_type = st.selectbox('Party Type', ['solo', 'duo', 'squad']) 
        size_map = {'solo': 1, 'duo': 2, 'squad': 4} 
        n = size_map[party_type] 
        st.caption(f'{n} player(s) required') 
    player_ids = [] 
    for i in range(n): 
        pid = st.number_input(f'Player {i+1} ID', min_value=1, step=1, key=f'p{i}') 
        player_ids.append(pid) 
    if st.button('Create Party', type='primary', use_container_width=True): 
        r = requests.post(f'{API}/parties/', 
                          json={'party_type': party_type, 'player_ids': player_ids}) 
        if r.status_code == 201: 
            data = r.json() 
            st.success(f'Party created! ID: {data["party_id"]}') 
            st.json(data) 
            st.session_state['last_party_id'] = data['party_id'] 
        else: 
            st.error(f'Error {r.status_code}: {r.text}') 
 
    st.divider() 
    st.markdown('### View Party Members') 
    lookup_pid = st.number_input('Party ID', min_value=1, step=1, key='lookup_party') 
    if st.button('Get Members'): 
        # Fetch Party Details first
        r_party = requests.get(f'{API}/parties/{lookup_pid}')
        if r_party.status_code == 200:
            st.json(r_party.json())
        else:
            st.error('Party not found')
            
        r = requests.get(f'{API}/parties/{lookup_pid}/members') 
        if r.status_code == 200: 
            members = r.json() 
            if members: 
                st.dataframe(pd.DataFrame(members), use_container_width=True) 
            else: 
                st.info('No members found') 
        elif r_party.status_code != 200: 
            # error already shown for party not found
            pass 
 
# ── Tab 2: Enter Queue ─────────────────────────────────────────── 
with tab2: 
    st.markdown('### Enter Matchmaking Queue') 
    col1, col2 = st.columns(2) 
    with col1: 
        q_party_id = st.number_input( 
            'Party ID', 
            min_value=1, step=1, 
            value=st.session_state.get('last_party_id', 1), 
            key='q_party') 
    with col2:
        mode_map = { 
            'Battle Royale Solo (mode 1)':  1, 
            'Battle Royale Duo (mode 2)':   2, 
            'Battle Royale Squad (mode 3)': 3, 
            'Ranked 5v5 (mode 4)':          4, 
            'Unranked 5v5 (mode 5)':        5, 
        } 
        mode_name = st.selectbox('Game Mode', list(mode_map.keys())) 
        mode_id = mode_map[mode_name] 
 
    if st.button('Enter Queue', type='primary', use_container_width=True): 
        r = requests.post(f'{API}/queue/', 
                          json={'party_id': q_party_id, 'mode_id': mode_id}) 
        if r.status_code == 202: 
            data = r.json() 
            st.success(f'Queued! Queue #: {data["queue_no"]}') 
            if data.get('match_id'): 
                st.balloons() 
                st.success(f'🎉 MATCH FOUND! Match ID: {data["match_id"]}') 
                st.session_state['last_match_id'] = data['match_id'] 
            else: 
                st.info('Waiting for more players... No match assembled yet.') 
        elif r.status_code == 409: 
            st.warning('This party is already in the queue for this mode') 
        else: 
            st.error(f'Error {r.status_code}: {r.text}') 

# ── Tab 3: Queue Monitor ───────────────────────────────────────── 
with tab3: 
    st.markdown('### Queues Exceeding Wait Time Limit') 
    st.caption('Parties shown here have been waiting longer than the configured max_wait_time') 
    if st.button('Refresh Monitor', use_container_width=True): 
        r = requests.get(f'{API}/queue/waiting-monitor') 
        if r.status_code == 200: 
            data = r.json() 
            if data: 
                df = pd.DataFrame(data) 
                st.dataframe(df, use_container_width=True) 
                st.warning(f'{len(data)} queue entries exceed wait time threshold') 
            else: 
                st.success('All queue entries within wait time limits') 
        else: 
            st.error(f'Error: {r.text}') 
    st.divider() 
    if st.button('Expire Timed-Out Queues', type='secondary', use_container_width=True): 
        r = requests.post(f'{API}/queue/expire-timeouts') 
        if r.status_code == 200: 
            data = r.json() 
            st.info(f"{data['expired']} queue entries marked as EXPIRED") 
        else: 
            st.error(f'Error: {r.text}')