import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

API = 'http://localhost:8000'

st.set_page_config(page_title='Engine Lab', page_icon='⚙️', layout='wide')
st.markdown('# ⚙️ Engine Lab')
st.markdown('> Configure matchmaking engines per game mode and compare lobby quality across engines')
st.divider()

tab1, tab2 = st.tabs(['🔧 Engine Configuration', '📊 Quality Comparison'])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TAB 1 — Engine Configuration
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab1:
    st.markdown('### Current Engine Assignments')
    st.caption('Each game mode is linked to a matchmaking criteria row, '
               'which references one engine. Change it here.')

    try:
        # Fetch available engines and mode-engine assignments
        engines_res = requests.get(f'{API}/engines/', timeout=5)
        modes_res   = requests.get(f'{API}/engines/modes', timeout=5)

        if engines_res.status_code != 200 or modes_res.status_code != 200:
            st.error('Failed to load engines or modes from API.')
            st.stop()

        engines_list = engines_res.json()
        modes_list   = modes_res.json()

        if not engines_list:
            st.warning('No engines found in MATCHMAKING_ENGINE table. '
                       'Run engine_seed.sql first.')
            st.stop()

        # Build engine lookup
        engine_options = {e['engine_id']: e['engine_name'] for e in engines_list
                          if e['is_active'] == 1}

        # ── Display current assignments ─────────────────────────────
        if modes_list:
            df_modes = pd.DataFrame(modes_list)
            display_cols = ['mode_id', 'mode_name', 'mode_type',
                            'team_size', 'max_players',
                            'engine_name', 'engine_id', 'criteria_id']
            available_cols = [c for c in display_cols if c in df_modes.columns]
            st.dataframe(
                df_modes[available_cols],
                use_container_width=True,
                hide_index=True,
                column_config={
                    'mode_id':      st.column_config.NumberColumn('Mode ID', width='small'),
                    'mode_name':    st.column_config.TextColumn('Mode Name'),
                    'mode_type':    st.column_config.TextColumn('Type'),
                    'engine_name':  st.column_config.TextColumn('Current Engine',
                                                                 help='Engine currently assigned'),
                    'engine_id':    st.column_config.NumberColumn('Eng ID', width='small'),
                    'criteria_id':  st.column_config.NumberColumn('Criteria ID', width='small'),
                },
            )
        else:
            st.info('No game modes found.')
            st.stop()

        # ── Change engine assignment ────────────────────────────────
        st.divider()
        st.markdown('### Change Engine for a Mode')

        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            mode_labels = {m['criteria_id']: f"{m['mode_name']}  (criteria {m['criteria_id']})"
                           for m in modes_list}
            selected_criteria = st.selectbox(
                'Select Mode (Criteria)',
                options=list(mode_labels.keys()),
                format_func=lambda x: mode_labels[x],
                key='engine_criteria_select',
            )

        with col2:
            selected_engine = st.selectbox(
                'New Engine',
                options=list(engine_options.keys()),
                format_func=lambda x: f"{engine_options[x]}  (ID {x})",
                key='engine_select',
            )

        with col3:
            st.markdown('<div style="height:28px"></div>', unsafe_allow_html=True)
            apply_btn = st.button('Apply', type='primary', use_container_width=True)

        if apply_btn:
            r = requests.put(
                f'{API}/engines/modes/{selected_criteria}/engine',
                json={'engine_id': selected_engine},
                timeout=5,
            )
            if r.status_code == 200:
                st.success(f'✅ Engine updated to **{engine_options[selected_engine]}** '
                           f'for criteria {selected_criteria}')
                st.rerun()
            else:
                st.error(f'Error {r.status_code}: {r.text}')

        # ── Engine parameters preview ───────────────────────────────
        st.divider()
        st.markdown('### Engine Parameters')
        # Show ALL engines here (including inactive) — viewing params is read-only
        all_engine_options = {e['engine_id']: e['engine_name'] for e in engines_list}
        preview_engine = st.selectbox(
            'View parameters for:',
            options=list(all_engine_options.keys()),
            format_func=lambda x: (f"{all_engine_options[x]}  (ID {x})"
                                   if x in engine_options
                                   else f"{all_engine_options[x]}  (ID {x}) — inactive"),
            key='param_preview',
        )
        try:
            params_res = requests.get(
                f'{API}/engines/{preview_engine}/parameters', timeout=5)
            if params_res.status_code == 200:
                params_data = params_res.json()
                if params_data:
                    df_params = pd.DataFrame(params_data)
                    st.dataframe(df_params, use_container_width=True, hide_index=True)
                else:
                    st.info('No parameters configured for this engine.')
            elif params_res.status_code == 404:
                st.info('No parameters configured for this engine.')
            else:
                st.error(f'Error: {params_res.text}')
        except requests.exceptions.ConnectionError:
            st.error('API is offline.')

    except requests.exceptions.ConnectionError:
        st.error('🔴 API is offline. Start the server with: '
                 '`uvicorn main:app --port 8000`')


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TAB 2 — Lobby Quality Comparison
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab2:
    st.markdown('### Compare Lobby Quality Across Engines')
    st.caption('Analyze how different matchmaking engines perform in terms of '
               'lobby fairness (MMR std dev, spread) over recent matches.')

    try:
        # Fetch modes for filter
        modes_res = requests.get(f'{API}/engines/modes', timeout=5)
        engines_res = requests.get(f'{API}/engines/', timeout=5)

        if modes_res.status_code != 200 or engines_res.status_code != 200:
            st.error('Failed to load modes/engines.')
            st.stop()

        modes_list = modes_res.json()
        engines_list = engines_res.json()

        # ── Filters ─────────────────────────────────────────────────
        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            mode_opts = {m['mode_id']: m['mode_name'] for m in modes_list}
            mode_opts_all = {0: '— All Modes —', **mode_opts}
            filter_mode = st.selectbox(
                'Game Mode',
                options=list(mode_opts_all.keys()),
                format_func=lambda x: mode_opts_all[x],
                key='qc_mode',
            )

        with col2:
            engine_opts = {e['engine_id']: e['engine_name'] for e in engines_list}
            engine_names_selected = st.multiselect(
                'Engines to compare',
                options=list(engine_opts.keys()),
                default=list(engine_opts.keys()),
                format_func=lambda x: engine_opts[x],
                key='qc_engines',
            )

        with col3:
            match_limit = st.slider('Recent matches', 10, 200, 50, key='qc_limit')

        if st.button('🔍 Load Comparison', type='primary', use_container_width=True):
            # Fetch batch lobby quality (no engine filter — we filter client-side)
            params = {'limit': match_limit}
            if filter_mode != 0:
                params['mode_id'] = filter_mode

            res = requests.get(f'{API}/engines/lobby-quality-batch',
                               params=params, timeout=30)

            if res.status_code != 200:
                st.error(f'API Error: {res.text}')
                st.stop()

            data = res.json()
            if not data:
                st.warning('No match data found for the selected filters.')
                st.stop()

            df = pd.DataFrame(data)
            df['m_start_time'] = pd.to_datetime(df['m_start_time'], format='ISO8601')

            # Filter to selected engines
            if engine_names_selected:
                df = df[df['engine_id'].isin(engine_names_selected)]

            if df.empty:
                st.warning('No matches found for the selected engines.')
                st.stop()

            # ── Summary metrics ─────────────────────────────────────
            st.divider()
            st.markdown('#### Summary by Engine')

            summary = df.groupby('engine_name').agg(
                matches=('match_id', 'count'),
                avg_std_dev=('mmr_std_dev', 'mean'),
                avg_spread=('mmr_spread', 'mean'),
                avg_lobby_mmr=('lobby_avg_mmr', 'mean'),
            ).round(2).reset_index()
            summary.columns = ['Engine', 'Matches', 'Avg Std Dev',
                                'Avg Spread', 'Avg Lobby MMR']

            # Highlight the best engine (lowest std dev)
            st.dataframe(summary, use_container_width=True, hide_index=True)

            best = summary.loc[summary['Avg Std Dev'].idxmin()]
            st.success(f'🏆 **{best["Engine"]}** has the fairest lobbies '
                       f'(avg std dev = {best["Avg Std Dev"]})')

            # ── Charts ──────────────────────────────────────────────
            st.divider()
            chart_col1, chart_col2 = st.columns(2)

            # Chart 1: MMR Std Dev over time
            with chart_col1:
                st.markdown('#### MMR Std Dev Over Time')
                st.caption('Lower = fairer matchmaking')
                fig1 = px.line(
                    df.sort_values('m_start_time'),
                    x='m_start_time', y='mmr_std_dev',
                    color='engine_name',
                    markers=True,
                    labels={
                        'm_start_time': 'Match Time',
                        'mmr_std_dev': 'MMR Std Dev',
                        'engine_name': 'Engine',
                    },
                    color_discrete_sequence=px.colors.qualitative.Set2,
                )
                fig1.update_layout(
                    plot_bgcolor='#161B22',
                    paper_bgcolor='#0D1117',
                    font_color='#E6EDF3',
                    legend=dict(orientation='h', yanchor='bottom',
                                y=1.02, xanchor='right', x=1),
                    height=400,
                )
                st.plotly_chart(fig1, use_container_width=True)

            # Chart 2: MMR Spread over time
            with chart_col2:
                st.markdown('#### MMR Spread Over Time')
                st.caption('Lower = tighter MMR range in lobby')
                fig2 = px.line(
                    df.sort_values('m_start_time'),
                    x='m_start_time', y='mmr_spread',
                    color='engine_name',
                    markers=True,
                    labels={
                        'm_start_time': 'Match Time',
                        'mmr_spread': 'MMR Spread',
                        'engine_name': 'Engine',
                    },
                    color_discrete_sequence=px.colors.qualitative.Set2,
                )
                fig2.update_layout(
                    plot_bgcolor='#161B22',
                    paper_bgcolor='#0D1117',
                    font_color='#E6EDF3',
                    legend=dict(orientation='h', yanchor='bottom',
                                y=1.02, xanchor='right', x=1),
                    height=400,
                )
                st.plotly_chart(fig2, use_container_width=True)

            # Chart 3: Box plot comparison
            st.divider()
            st.markdown('#### Distribution Comparison')
            box_col1, box_col2 = st.columns(2)

            with box_col1:
                fig3 = px.box(
                    df, x='engine_name', y='mmr_std_dev',
                    color='engine_name',
                    labels={
                        'engine_name': 'Engine',
                        'mmr_std_dev': 'MMR Std Dev',
                    },
                    title='Std Dev Distribution by Engine',
                    color_discrete_sequence=px.colors.qualitative.Set2,
                )
                fig3.update_layout(
                    plot_bgcolor='#161B22',
                    paper_bgcolor='#0D1117',
                    font_color='#E6EDF3',
                    showlegend=False,
                    height=400,
                )
                st.plotly_chart(fig3, use_container_width=True)

            with box_col2:
                fig4 = px.box(
                    df, x='engine_name', y='mmr_spread',
                    color='engine_name',
                    labels={
                        'engine_name': 'Engine',
                        'mmr_spread': 'MMR Spread',
                    },
                    title='Spread Distribution by Engine',
                    color_discrete_sequence=px.colors.qualitative.Set2,
                )
                fig4.update_layout(
                    plot_bgcolor='#161B22',
                    paper_bgcolor='#0D1117',
                    font_color='#E6EDF3',
                    showlegend=False,
                    height=400,
                )
                st.plotly_chart(fig4, use_container_width=True)

            # ── Per-match detail table ──────────────────────────────
            st.divider()
            st.markdown('#### Match-Level Detail')
            detail_cols = ['match_id', 'engine_name', 'mode_name',
                           'lobby_avg_mmr', 'mmr_std_dev', 'mmr_spread',
                           'team_count', 'm_start_time']
            available = [c for c in detail_cols if c in df.columns]
            st.dataframe(
                df[available].sort_values('m_start_time', ascending=False),
                use_container_width=True,
                hide_index=True,
            )

    except requests.exceptions.ConnectionError:
        st.error('🔴 API is offline. Start the server with: '
                 '`uvicorn main:app --port 8000`')
