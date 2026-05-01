-- SYSTEM_ROLE  ids: 1=player  2=moderator  3=admin 
INSERT INTO SYSTEM_ROLE VALUES (seq_sys_role.NEXTVAL,'player'); 
INSERT INTO SYSTEM_ROLE VALUES (seq_sys_role.NEXTVAL,'moderator'); 
INSERT INTO SYSTEM_ROLE VALUES (seq_sys_role.NEXTVAL,'admin'); 
 -- ROLE  ids: 1=tank  2=support  3=dps  4=scout  5=fragger 
INSERT INTO ROLE VALUES (seq_role.NEXTVAL,'tank'); 
INSERT INTO ROLE VALUES (seq_role.NEXTVAL,'support'); 
INSERT INTO ROLE VALUES (seq_role.NEXTVAL,'dps'); 
INSERT INTO ROLE VALUES (seq_role.NEXTVAL,'scout'); 
INSERT INTO ROLE VALUES (seq_role.NEXTVAL,'fragger'); 
 -- GAME_MODE  ids: 1=BR_Solo  2=BR_Duo  3=BR_Squad  4=Ranked5v5  5=Unranked5v5 
INSERT INTO GAME_MODE VALUES (seq_game_mode.NEXTVAL,'Battle_Royale_Solo',  1,100,'battle_royale'); 
INSERT INTO GAME_MODE VALUES (seq_game_mode.NEXTVAL,'Battle_Royale_Duo',   2,100,'battle_royale'); 
INSERT INTO GAME_MODE VALUES (seq_game_mode.NEXTVAL,'Battle_Royale_Squad', 4,100,'battle_royale'); 
INSERT INTO GAME_MODE VALUES (seq_game_mode.NEXTVAL,'Ranked_5v5',          5, 10,'competitive'); 
INSERT INTO GAME_MODE VALUES (seq_game_mode.NEXTVAL,'Unranked_5v5',        5, 10,'competitive'); 
 -- MATCHMAKING_CRITERIA  (criteria_id, max_mm_diff, max_wait_secs, priority_type, mode_id) 
INSERT INTO MATCHMAKING_CRITERIA VALUES (seq_mm_criteria.NEXTVAL,200,120,'mmr_strict',   1); 
INSERT INTO MATCHMAKING_CRITERIA VALUES (seq_mm_criteria.NEXTVAL,200,120,'mmr_strict',   2); 
INSERT INTO MATCHMAKING_CRITERIA VALUES (seq_mm_criteria.NEXTVAL,200,120,'mmr_strict',   3); 
INSERT INTO MATCHMAKING_CRITERIA VALUES (seq_mm_criteria.NEXTVAL,150, 90,'mmr_strict',   4); 
INSERT INTO MATCHMAKING_CRITERIA VALUES (seq_mm_criteria.NEXTVAL,300,180,'wait_balanced',5); 
 
COMMIT; 