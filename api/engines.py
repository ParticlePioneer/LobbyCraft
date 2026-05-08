from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dal import engine_dal

router = APIRouter()


class EngineAssignment(BaseModel):
    engine_id: int


@router.get('/')
def list_engines():
    """List all matchmaking engines."""
    return engine_dal.get_all_engines()


# ── Static path routes MUST come before /{engine_id} parameterized routes ──

@router.get('/modes')
def modes_with_engines():
    """List all game modes with their currently assigned engine."""
    return engine_dal.get_modes_with_engine()


@router.put('/modes/{criteria_id}/engine')
def assign_engine(criteria_id: int, body: EngineAssignment):
    """
    Change the matchmaking engine for a specific criteria (mode).
    Accepts criteria_id (not mode_id) because a mode may have
    multiple criteria rows in future.
    """
    # Verify the engine exists and is active
    engines = engine_dal.get_all_engines()
    valid_ids = [e['engine_id'] for e in engines if e['is_active'] == 1]
    if body.engine_id not in valid_ids:
        raise HTTPException(
            400, f'Engine {body.engine_id} not found or inactive. '
                 f'Active engines: {valid_ids}')
    n = engine_dal.update_mode_engine(criteria_id, body.engine_id)
    if n == 0:
        raise HTTPException(404, f'Criteria {criteria_id} not found')
    return {
        'status': 'updated',
        'criteria_id': criteria_id,
        'new_engine_id': body.engine_id,
    }


@router.get('/lobby-quality-batch')
def lobby_quality_batch(mode_id: int = None, engine_id: int = None,
                        limit: int = 50):
    """
    Batch lobby quality metrics for recent matches,
    optionally filtered by mode and/or engine.
    """
    return engine_dal.get_lobby_quality_batch(
        mode_id=mode_id, engine_id=engine_id, limit=limit)


# ── Parameterized route LAST to avoid conflicts ──────────────────

@router.get('/{engine_id}/parameters')
def engine_params(engine_id: int):
    """List all tunable parameters for an engine."""
    params = engine_dal.get_engine_params(engine_id)
    if not params:
        raise HTTPException(404, f'No parameters found for engine {engine_id}')
    return params
