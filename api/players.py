from fastapi import APIRouter, HTTPException 
from pydantic import BaseModel 
from dal import player_dal 
import oracledb

router = APIRouter() 

class PlayerCreate(BaseModel): 
    username: str 
    region: str 

class RolePref(BaseModel): 
    role_id: int 
    priority: int 

@router.post('/', status_code=201) 
def create_player(body: PlayerCreate): 
    try:
        return player_dal.create_player(body.username, body.region).__dict__ 
    except oracledb.IntegrityError:
        raise HTTPException(status_code=409, detail="Username already exists")
 
@router.get('/{player_id}') 
def get_player(player_id: int): 
    p = player_dal.get_player(player_id) 
    if not p: raise HTTPException(404, 'Not found') 
    return p.__dict__ 
 
@router.get('/{player_id}/mmr-history') 
def mmr_history(player_id: int): 
    return player_dal.get_mmr_history(player_id) 
 
@router.post('/{player_id}/role-preferences', status_code=201) 
def set_role_pref(player_id: int, body: RolePref): 
    player_dal.set_role_preference(player_id, body.role_id, body.priority) 
    return {'status': 'ok'} 
