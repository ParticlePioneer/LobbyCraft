import streamlit as st
import requests
import pandas as pd

API = 'http://localhost:8000'

st.set_page_config(page_title='Analytics', page_icon='📊', layout='wide')

st.title('📊 Analytics & Dashboards')

tab1, tab2, tab3 = st.tabs(['🏆 Leaderboards', '⚖️ Lobby Quality', '📈 MMR History'])

with tab1:
    st.subheader('Top Killers')
    mode_type = st.selectbox('Game Mode', ['battle_royale', 'competitive'])
    limit = st.slider('Top N Players', 5, 50, 10)
    
    if st.button('Load Leaderboard'):
        try:
            res = requests.get(f'{API}/matches/leaderboard/kills?mode_type={mode_type}&limit={limit}')
            if res.status_code == 200:
                data = res.json()
                if data:
                    df = pd.DataFrame(data)
                    st.dataframe(df, use_container_width=True)
                    
                    # Display a bar chart
                    chart_data = df.set_index('username')[['total_kills']]
                    st.bar_chart(chart_data)
                else:
                    st.info('No data for this mode.')
            else:
                st.error('Failed to load leaderboard.')
        except requests.exceptions.ConnectionError:
            st.error('API is offline. Please start the server.')

with tab2:
    st.subheader('Matchmaking Fairness (Lobby Quality)')
    st.markdown('Analyze the MMR distribution for a specific match.')
    match_id = st.number_input('Match ID', min_value=1, step=1, key='lobby_match_id')
    
    if st.button('Analyze Match'):
        try:
            res = requests.get(f'{API}/matches/{match_id}/lobby-quality')
            if res.status_code == 200:
                data = res.json()
                if data and 'lobby_avg_mmr' in data:
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Avg MMR", data.get('lobby_avg_mmr'))
                    col2.metric("MMR Spread", data.get('mmr_spread'))
                    col3.metric("Std Dev", data.get('mmr_std_dev'))
                else:
                    st.warning("No teams found for this match.")
            else:
                st.error("Failed to fetch lobby quality.")
        except requests.exceptions.ConnectionError:
            st.error('API is offline. Please start the server.')

with tab3:
    st.subheader('Player MMR History')
    player_id = st.number_input('Player ID', min_value=1, step=1, key='mmr_player_id')
    
    if st.button('View History'):
        try:
            res = requests.get(f'{API}/players/{player_id}/mmr-history')
            if res.status_code == 200:
                data = res.json()
                if data:
                    df = pd.DataFrame(data)
                    st.dataframe(df, use_container_width=True)
                    
                    if 'mmr_after' in df.columns and 'm_start_time' in df.columns:
                        df['m_start_time'] = pd.to_datetime(df['m_start_time'])
                        chart_data = df.set_index('m_start_time')[['mmr_after']]
                        st.line_chart(chart_data)
                else:
                    st.info('No match history found for this player.')
            else:
                st.error('Failed to fetch MMR history.')
        except requests.exceptions.ConnectionError:
            st.error('API is offline. Please start the server.')
