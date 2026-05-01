import streamlit as st
import requests
import random

API = 'http://localhost:8000'

st.set_page_config(page_title='Match Results', page_icon='🏆', layout='wide')

st.title('🏆 Match Results')
st.markdown('Submit post-match statistics or view completed match details.')

tab1, tab2 = st.tabs(['📝 Submit Results', '🔍 View Match Details'])

with tab1:
    st.subheader('Auto-Generate & Submit Stats (Test Mode)')
    st.markdown('Automatically generate random stats for all participants in a match.')
    match_id_submit = st.number_input('Match ID', min_value=1, step=1, key='submit_match_id')
    
    if st.button('Auto-Generate & Submit Results', type='primary'):
        try:
            # fetch participants
            r_part = requests.get(f'{API}/matches/{match_id_submit}/participants')
            if r_part.status_code == 200:
                participants = r_part.json()
                if not participants:
                    st.error("No participants found for this match.")
                else:
                    payload = {"participants": []}
                    roles = ['DPS', 'Tank', 'Support', 'Flex']
                    for idx, p in enumerate(participants):
                        is_winner = random.choice([0, 1]) 
                        payload["participants"].append({
                            "player_id": p['player_id'],
                            "placement": random.randint(1, 10),
                            "survival_time": random.randint(300, 1800),
                            "kills": random.randint(0, 15),
                            "assists": random.randint(0, 10),
                            "revives": random.randint(0, 3),
                            "damage_done": random.randint(500, 5000),
                            "damage_taken": random.randint(500, 4000),
                            "is_winner": is_winner,
                            "role_used": random.choice(roles)
                        })
                    res = requests.post(f'{API}/matches/{match_id_submit}/result', json=payload)
                    if res.status_code == 200:
                        st.success(f'Successfully auto-generated and submitted results for {len(participants)} players! Match finalised.')
                        with st.expander('View Generated Payload'):
                            st.json(payload)
                    else:
                        st.error(f'Error submitting: {res.text}')
            else:
                st.error(f'Could not fetch participants: {r_part.text}')
        except requests.exceptions.ConnectionError:
            st.error('API is offline. Please start the server.')

with tab2:
    st.subheader('Look up Match')
    match_id_view = st.number_input('Enter Match ID', min_value=1, step=1, key='view_match_id')
    
    if st.button('Fetch Details'):
        try:
            res = requests.get(f'{API}/matches/{match_id_view}')
            if res.status_code == 200:
                match_data = res.json()
                st.json(match_data)
            else:
                st.error('Match not found or error occurred.')
        except requests.exceptions.ConnectionError:
            st.error('API is offline. Please start the server.')
