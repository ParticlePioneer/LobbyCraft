from fastapi import APIRouter, HTTPException 
from pydantic import BaseModel 
from dal import party_dal 
 
router = APIRouter() 
 
class PartyCreate(BaseModel): 
    party_type: str 
    player_ids: list 
 
@router.post('/', status_code=201) 
def create_party(body: PartyCreate): 
    if body.party_type not in ('solo','duo','squad'): 
        raise HTTPException(400, 'party_type must be solo, duo, or squad') 
    return party_dal.create_party(body.party_type, body.player_ids).__dict__ 
 
@router.get('/{party_id}') 
def get_party(party_id: int): 
    p = party_dal.get_party(party_id) 
    if not p: raise HTTPException(404, 'Not found') 
    return p.__dict__ 
 
@router.get('/{party_id}/members') 
def get_members(party_id: int): 
    return [m.__dict__ for m in party_dal.get_party_members(party_id)] 
