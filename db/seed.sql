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
 -- MATCHMAKING_CRITERIA  (criteria_id, max_mm_diff, max_wait_secs, priority_type, mode_id, engine_id) 
INSERT INTO MATCHMAKING_CRITERIA VALUES (seq_mm_criteria.NEXTVAL,200,120,'mmr_strict',   1,   1); 
INSERT INTO MATCHMAKING_CRITERIA VALUES (seq_mm_criteria.NEXTVAL,200,120,'mmr_strict',   2,   1); 
INSERT INTO MATCHMAKING_CRITERIA VALUES (seq_mm_criteria.NEXTVAL,200,120,'mmr_strict',   3,   1); 
INSERT INTO MATCHMAKING_CRITERIA VALUES (seq_mm_criteria.NEXTVAL,150, 90,'mmr_strict',   4,   1); 
INSERT INTO MATCHMAKING_CRITERIA VALUES (seq_mm_criteria.NEXTVAL,300,180,'wait_balanced',5,   2); 
  -- Register engines
INSERT INTO MATCHMAKING_ENGINE VALUES (seq_engine.NEXTVAL,'mmr_based','engine.mmr_engine.MMREngine', 1);
INSERT INTO MATCHMAKING_ENGINE VALUES (seq_engine.NEXTVAL,'bucket','engine.bucket_engine.BucketEngine', 1);
INSERT INTO MATCHMAKING_ENGINE VALUES (seq_engine.NEXTVAL,'glicko2','engine.glicko_rating.Glicko2Rating', 0);
-- Engine parameters
INSERT INTO ENGINE_PARAMETER VALUES (seq_param.NEXTVAL,1,'max_mmr_diff','200','int');
INSERT INTO ENGINE_PARAMETER VALUES (seq_param.NEXTVAL,1,'k_factor','32','int');
INSERT INTO ENGINE_PARAMETER VALUES (seq_param.NEXTVAL,1,'delta_cap','50','int');
INSERT INTO ENGINE_PARAMETER VALUES (seq_param.NEXTVAL,1,'mmr_floor','0','int');
INSERT INTO ENGINE_PARAMETER VALUES (seq_param.NEXTVAL,1,'rating_engine_class','engine.elo_rating.EloRating','string');
INSERT INTO ENGINE_PARAMETER VALUES (seq_param.NEXTVAL,2,'max_mmr_diff','250','int');
INSERT INTO ENGINE_PARAMETER VALUES (seq_param.NEXTVAL,2,'bucket_size','250','int');
INSERT INTO ENGINE_PARAMETER VALUES (seq_param.NEXTVAL,2,'bucket_overlap','50','int');
INSERT INTO ENGINE_PARAMETER VALUES (seq_param.NEXTVAL,2,'delta_cap','30','int');
INSERT INTO ENGINE_PARAMETER VALUES (seq_param.NEXTVAL,2,'rating_engine_class','engine.flat_rating.FlatRating','string');
INSERT INTO ENGINE_PARAMETER VALUES (seq_param.NEXTVAL,3,'tau','0.5','float');
INSERT INTO ENGINE_PARAMETER VALUES (seq_param.NEXTVAL,3,'initial_rd','350.0','float');
INSERT INTO ENGINE_PARAMETER VALUES (seq_param.NEXTVAL,3,'initial_vol','0.06','float');
INSERT INTO ENGINE_PARAMETER VALUES (seq_param.NEXTVAL,3,'rating_engine_class','engine.glicko_rating.Glicko2Rating','string');

COMMIT; 