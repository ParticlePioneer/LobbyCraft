from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dal.player_dal import create_player, get_player, update_mmr, get_mmr_history, set_role_preference

router = APIRouter()

# ── Request schemas ──────────────────────────────────────────────
class CreatePlayerReq(BaseModel):
    username: str
    region: str
    sys_role_id: int = 1

class UpdateMMRReq(BaseModel):
    delta: int

class RolePrefReq(BaseModel):
    role_id: int
    priority: int

# ── Endpoints ────────────────────────────────────────────────────
@router.post('/', status_code=201)
def api_create_player(body: CreatePlayerReq):
    try:
        p = create_player(body.username, body.region, body.sys_role_id)
        return p.__dict__
    except Exception as e:
        if 'UQ_PL_UNAME' in str(e):
            raise HTTPException(409, 'Username already exists')
        raise

@router.get('/{player_id}')
def api_get_player(player_id: int):
    p = get_player(player_id)
    if not p:
        raise HTTPException(404, 'Player not found')
    return p.__dict__

@router.patch('/{player_id}/mmr')
def api_update_mmr(player_id: int, body: UpdateMMRReq):
    update_mmr(player_id, body.delta)
    return get_player(player_id).__dict__

@router.get('/{player_id}/mmr-history')
def api_mmr_history(player_id: int):
    return get_mmr_history(player_id)

@router.put('/{player_id}/role-preference')
def api_set_role_pref(player_id: int, body: RolePrefReq):
    set_role_preference(player_id, body.role_id, body.priority)
    return {'status': 'ok'}
