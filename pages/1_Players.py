import streamlit as st 
import requests 
import pandas as pd 
import plotly.express as px 
 
API = 'http://localhost:8000' 
 
st.set_page_config(page_title='Players', page_icon='👤', layout='wide') 
st.markdown('# 👤 Player Management') 
st.divider() 
 
tab1, tab2, tab3 = st.tabs(['Create Player', 'View Player', 'MMR History']) 
 
# ── Tab 1: Create Player ───────────────────────────────────────── 
with tab1: 
    st.markdown('### Register New Player') 
    col1, col2 = st.columns(2) 
    with col1: 
        username = st.text_input('Username', placeholder='ProSniper99') 
        region = st.selectbox('Region', ['AS-EAST', 'EU-WEST', 'NA-EAST', 'NA-WEST', 'SA-EAST']) 
    with col2: 
        st.markdown('**Default Stats**') 
        st.metric('Starting MMR', '1000') 
        st.metric('System Role', 'player') 
 
    if st.button('Create Player', type='primary', use_container_width=True): 
        if not username: 
            st.error('Username is required') 
        else: 
            r = requests.post(f'{API}/players/', json={'username': username, 'region': region}) 
            if r.status_code == 201: 
                data = r.json() 
                st.success(f'Player created! ID: {data["player_id"]}') 
                st.json(data) 
            elif r.status_code == 422 or r.status_code == 400: 
                st.error('Username already exists or invalid input') 
            else: 
                st.error(f'Error {r.status_code}: {r.text}') 
 
# ── Tab 2: View Player ─────────────────────────────────────────── 
with tab2: 
    st.markdown('### Look Up Player') 
    pid = st.number_input('Player ID', min_value=1, step=1, value=1) 
    if st.button('Fetch Player', use_container_width=True): 
        r = requests.get(f'{API}/players/{pid}') 
        if r.status_code == 200: 
            data = r.json() 
            col1, col2, col3 = st.columns(3) 
            col1.metric('Username', data['username']) 
            col2.metric('Current MMR', data['current_mmr']) 
            col3.metric('Region', data['region']) 
            st.json(data) 
        else: 
            st.warning('Player not found') 
 
    st.divider() 
    st.markdown('### Set Role Preference') 
    col1, col2, col3 = st.columns(3) 
    with col1: 
        rp_pid = st.number_input('Player ID', min_value=1, step=1, value=1, key='rp_pid')
    with col2: 
         role_map = {'tank': 1, 'support': 2, 'dps': 3, 'scout': 4, 'fragger': 5} 
         role_name = st.selectbox('Role', list(role_map.keys())) 
    with col3: 
        priority = st.selectbox('Priority', [1, 2, 3], help='1 = highest') 
    if st.button('Save Preference', use_container_width=True): 
        r = requests.post(f'{API}/players/{rp_pid}/role-preferences', 
                          json={'role_id': role_map[role_name], 'priority': priority}) 
        if r.status_code == 201: 
            st.success('Role preference saved') 
        else: 
            st.error(f'Error: {r.text}') 

# ── Tab 3: MMR History ─────────────────────────────────────────── 
with tab3: 
    st.markdown('### MMR History') 
    h_pid = st.number_input('Player ID', min_value=1, step=1, value=1, key='h_pid') 
    if st.button('Load MMR History', type='primary', use_container_width=True): 
        r = requests.get(f'{API}/players/{h_pid}/mmr-history') 
        if r.status_code == 200: 
            history = r.json() 
            if not history: 
                st.info('No match history yet for this player') 
            else: 
                df = pd.DataFrame(history) 
                # Line chart 
                fig = px.line( 
                    df, x='m_start_time', y='mmr_after', 
                    title=f'MMR Progression — Player {h_pid}', 
                    labels={'m_start_time': 'Match Date', 'mmr_after': 'MMR'}, 
                    markers=True, 
                    color_discrete_sequence=['#58A6FF'], 
                ) 
                fig.update_layout( 
                    plot_bgcolor='#161B22', 
                    paper_bgcolor='#0D1117', 
                    font_color='#E6EDF3', 
                ) 
                st.plotly_chart(fig, use_container_width=True) 
                # Delta column colouring 
                df['delta_display'] = df['mmr_delta'].apply( 
                    lambda x: f'+{x}' if x > 0 else str(x)) 
                st.dataframe( 
                    df[['match_id','m_start_time','mmr_before','mmr_delta','mmr_after']], 
                    use_container_width=True, 
                ) 
        else: 
            st.error(f'Error: {r.text}') 

