CREATE SEQUENCE seq_sys_role    START WITH 1 INCREMENT BY 1 NOCACHE NOCYCLE; 
CREATE SEQUENCE seq_role        START WITH 1 INCREMENT BY 1 NOCACHE NOCYCLE; 
CREATE SEQUENCE seq_game_mode   START WITH 1 INCREMENT BY 1 NOCACHE NOCYCLE; 
CREATE SEQUENCE seq_player      START WITH 1 INCREMENT BY 1 NOCACHE NOCYCLE; 
CREATE SEQUENCE seq_party       START WITH 1 INCREMENT BY 1 NOCACHE NOCYCLE; 
CREATE SEQUENCE seq_mm_criteria START WITH 1 INCREMENT BY 1 NOCACHE NOCYCLE; 
CREATE SEQUENCE seq_mm_session  START WITH 1 INCREMENT BY 1 NOCACHE NOCYCLE; 
CREATE SEQUENCE seq_queue       START WITH 1 INCREMENT BY 1 NOCACHE NOCYCLE; 
CREATE SEQUENCE seq_match       START WITH 1 INCREMENT BY 1 NOCACHE NOCYCLE; 
CREATE SEQUENCE seq_team        START WITH 1 INCREMENT BY 1 NOCACHE NOCYCLE; 


CREATE TABLE SYSTEM_ROLE ( 
    sys_role_id   NUMBER        CONSTRAINT pk_sys_role PRIMARY KEY, 
    sys_role_name VARCHAR2(15)  NOT NULL, 
    CONSTRAINT uq_sr_name UNIQUE (sys_role_name), 
    CONSTRAINT ck_sr_name CHECK (sys_role_name IN ('player','moderator','admin')) 
); 
CREATE TABLE ROLE ( 
    role_id   NUMBER       CONSTRAINT pk_role PRIMARY KEY, 
    role_name VARCHAR2(20) NOT NULL, 
    CONSTRAINT uq_role_name UNIQUE (role_name) 
); 
CREATE TABLE GAME_MODE ( 
    mode_id     NUMBER        CONSTRAINT pk_game_mode PRIMARY KEY, 
    mode_name   VARCHAR2(30)  NOT NULL, 
    team_size   NUMBER(2)     NOT NULL, 
    max_players NUMBER(3)     NOT NULL, 
    mode_type   VARCHAR2(15)  NOT NULL, 
    CONSTRAINT uq_gm_name UNIQUE (mode_name), 
    CONSTRAINT ck_gm_type CHECK (mode_type IN ('battle_royale','competitive')) 
); 
CREATE TABLE PLAYER ( 
    player_id   NUMBER        CONSTRAINT pk_player PRIMARY KEY, 
    username    VARCHAR2(50)  NOT NULL, 
    region      VARCHAR2(10)  NOT NULL, 
    join_date   DATE          DEFAULT SYSDATE NOT NULL, 
    current_mmr NUMBER(6)     DEFAULT 1000    NOT NULL, 
    sys_role_id NUMBER        NOT NULL, 
    CONSTRAINT uq_pl_uname   UNIQUE (username), 
    CONSTRAINT fk_pl_sysrole FOREIGN KEY (sys_role_id) REFERENCES SYSTEM_ROLE(sys_role_id) 
); 
CREATE TABLE PARTY ( 
    party_id   NUMBER       CONSTRAINT pk_party PRIMARY KEY, 
    created_at TIMESTAMP    DEFAULT SYSTIMESTAMP NOT NULL, 
    party_type VARCHAR2(10) NOT NULL, 
    CONSTRAINT ck_pa_type CHECK (party_type IN ('solo','duo','squad')) 
); 
CREATE TABLE PARTY_MEMBER ( 
    party_id    NUMBER NOT NULL, 
    player_id   NUMBER NOT NULL, 
    member_role VARCHAR2(20), 
    CONSTRAINT pk_party_member PRIMARY KEY (party_id, player_id), 
    CONSTRAINT fk_pm_party  FOREIGN KEY (party_id)  REFERENCES PARTY(party_id), 
    CONSTRAINT fk_pm_player FOREIGN KEY (player_id) REFERENCES PLAYER(player_id)
);
CREATE TABLE ROLE_PREFERENCE ( 
    player_id NUMBER    NOT NULL, 
    role_id   NUMBER    NOT NULL, 
    priority  NUMBER(1) NOT NULL, 
    CONSTRAINT pk_role_pref PRIMARY KEY (player_id, role_id), 
    CONSTRAINT fk_rp_player FOREIGN KEY (player_id) REFERENCES PLAYER(player_id), 
    CONSTRAINT fk_rp_role   FOREIGN KEY (role_id)   REFERENCES ROLE(role_id) 
); 
CREATE TABLE MATCHMAKING_CRITERIA ( 
    criteria_id   NUMBER       CONSTRAINT pk_mm_crit PRIMARY KEY, 
    max_mm_diff   NUMBER(5)    NOT NULL, 
    max_wait_time NUMBER(5)    NOT NULL, 
    priority_type VARCHAR2(15) NOT NULL, 
    mode_id       NUMBER       NOT NULL, 
    CONSTRAINT fk_mc_mode FOREIGN KEY (mode_id) REFERENCES GAME_MODE(mode_id) 
); 
CREATE TABLE MATCHMAKING_SESSION ( 
    session_id  NUMBER       CONSTRAINT pk_mm_session PRIMARY KEY, 
    start_time  TIMESTAMP    DEFAULT SYSTIMESTAMP NOT NULL, 
    end_time    TIMESTAMP, 
    status      VARCHAR2(12) NOT NULL, 
    criteria_id NUMBER       NOT NULL, 
    CONSTRAINT ck_ms_status CHECK (status IN ('SEARCHING','ASSEMBLING','COMPLETED','FAILED')), 
    CONSTRAINT fk_ms_crit FOREIGN KEY (criteria_id) REFERENCES MATCHMAKING_CRITERIA(criteria_id) 
); 
CREATE TABLE QUEUE ( 
    queue_no     NUMBER       CONSTRAINT pk_queue PRIMARY KEY, 
    queue_type   VARCHAR2(20) NOT NULL, 
    enqueue_time TIMESTAMP    DEFAULT SYSTIMESTAMP NOT NULL, 
    party_id     NUMBER       NOT NULL, 
    mode_id      NUMBER       NOT NULL, 
    status       VARCHAR2(10) DEFAULT 'WAITING' NOT NULL, 
    CONSTRAINT ck_q_status CHECK (status IN ('WAITING','MATCHED','EXPIRED')), 
    CONSTRAINT fk_q_party FOREIGN KEY (party_id) REFERENCES PARTY(party_id), 
    CONSTRAINT fk_q_mode  FOREIGN KEY (mode_id)  REFERENCES GAME_MODE(mode_id) 
); 
CREATE TABLE MATCH ( 
    match_id     NUMBER       CONSTRAINT pk_match PRIMARY KEY, 
    match_region VARCHAR2(10) NOT NULL, 
    status       VARCHAR2(10) NOT NULL, 
    m_start_time TIMESTAMP    NOT NULL, 
    m_end_time   TIMESTAMP, 
    match_mmr    NUMBER(6)    NOT NULL, 
    session_id   NUMBER       NOT NULL, 
    mode_id      NUMBER       NOT NULL, 
    CONSTRAINT uq_m_session UNIQUE (session_id), 
    CONSTRAINT ck_m_status  CHECK (status IN ('PENDING','LIVE','COMPLETED','CANCELLED')), 
    CONSTRAINT fk_m_session FOREIGN KEY (session_id) REFERENCES MATCHMAKING_SESSION(session_id), 
    CONSTRAINT fk_m_mode    FOREIGN KEY (mode_id)    REFERENCES GAME_MODE(mode_id) 
); 
CREATE TABLE TEAM ( 
    team_id      NUMBER    CONSTRAINT pk_team PRIMARY KEY, 
    match_id     NUMBER    NOT NULL, 
    team_number  NUMBER(3) NOT NULL, 
    avg_team_mmr NUMBER(6) NOT NULL, 
    CONSTRAINT fk_t_match FOREIGN KEY (match_id) REFERENCES MATCH(match_id) 
); 
CREATE TABLE MATCH_PARTICIPANT ( 
    player_id     NUMBER    NOT NULL, 
    match_id      NUMBER    NOT NULL, 
    team_id       NUMBER    NOT NULL, 
    role_used     VARCHAR2(20), 
    placement     NUMBER(3) NOT NULL, 
    survival_time NUMBER(6) DEFAULT 0 NOT NULL, 
    kills         NUMBER(3) DEFAULT 0 NOT NULL, 
    assists       NUMBER(3) DEFAULT 0 NOT NULL, 
    revives       NUMBER(3) DEFAULT 0 NOT NULL, 
    damage_done   NUMBER(8) DEFAULT 0 NOT NULL, 
    damage_taken  NUMBER(8) DEFAULT 0 NOT NULL, 
    is_winner     NUMBER(1) DEFAULT 0 NOT NULL, 
    mmr_before    NUMBER(6) NOT NULL, 
    mmr_delta     NUMBER(5) DEFAULT 0 NOT NULL, 
    CONSTRAINT pk_match_part PRIMARY KEY (player_id, match_id), 
    CONSTRAINT ck_mp_winner CHECK (is_winner IN (0,1)), 
    CONSTRAINT fk_mp_player FOREIGN KEY (player_id) REFERENCES PLAYER(player_id), 
    CONSTRAINT fk_mp_match  FOREIGN KEY (match_id)  REFERENCES MATCH(match_id), 
    CONSTRAINT fk_mp_team   FOREIGN KEY (team_id)   REFERENCES TEAM(team_id)
);
CREATE INDEX idx_player_mmr    ON PLAYER(current_mmr); 
CREATE INDEX idx_player_region ON PLAYER(region); 
CREATE INDEX idx_queue_status  ON QUEUE(status, mode_id, enqueue_time); 
CREATE INDEX idx_queue_party   ON QUEUE(party_id); 
CREATE INDEX idx_mp_player     ON MATCH_PARTICIPANT(player_id); 
CREATE INDEX idx_team_match    ON TEAM(match_id); 
CREATE INDEX idx_ms_status     ON MATCHMAKING_SESSION(status); 

