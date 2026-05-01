CREATE OR REPLACE PROCEDURE sp_create_session ( 
    p_criteria_id IN  NUMBER, 
    p_session_id  OUT NUMBER 
) AS 
BEGIN 
    SELECT seq_mm_session.NEXTVAL INTO p_session_id FROM DUAL; 
    INSERT INTO MATCHMAKING_SESSION (session_id, status, criteria_id) 
    VALUES (p_session_id, 'SEARCHING', p_criteria_id); 
    COMMIT; 
EXCEPTION WHEN OTHERS THEN ROLLBACK; RAISE; 
END sp_create_session; 
/ 
 
CREATE OR REPLACE PROCEDURE sp_expire_stale (p_count OUT NUMBER) AS 
BEGIN 
    UPDATE QUEUE q SET q.status = 'EXPIRED' 
    WHERE  q.status = 'WAITING' 
    AND    (SYSDATE - CAST(q.enqueue_time AS DATE)) * 86400 > ( 
        SELECT mc.max_wait_time FROM MATCHMAKING_CRITERIA mc 
        WHERE mc.mode_id = q.mode_id AND ROWNUM = 1); 
    p_count := SQL%ROWCOUNT; 
    COMMIT; 
EXCEPTION WHEN OTHERS THEN ROLLBACK; RAISE; 
END sp_expire_stale; 
/ 
 
CREATE OR REPLACE PROCEDURE sp_finalise_match ( 
    p_match_id IN NUMBER, p_session_id IN NUMBER 
) AS 
BEGIN 
    UPDATE MATCH SET status='COMPLETED', m_end_time=SYSTIMESTAMP 
    WHERE match_id = p_match_id; 
    UPDATE MATCHMAKING_SESSION SET status='COMPLETED', end_time=SYSTIMESTAMP 
    WHERE session_id = p_session_id; 
    COMMIT; 
EXCEPTION WHEN OTHERS THEN ROLLBACK; RAISE; 
END sp_finalise_match; 
/ 