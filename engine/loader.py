import importlib
from db.connection import get_conn


def _fetch_engine_record(engine_id: int) -> tuple:
    """
    Fetch engine class path and parameters from DB.

    Returns:
        (engine_name: str, class_path: str, params: dict)

    Raises:
        ValueError if engine_id not found or engine is inactive.
    """
    with get_conn() as conn:
        cur = conn.cursor()

        # Fetch engine metadata
        cur.execute(
            '''SELECT engine_name, engine_class
               FROM   MATCHMAKING_ENGINE
               WHERE  engine_id = :1
               AND    is_active  = 1''',
            [engine_id]
        )
        row = cur.fetchone()
        if not row:
            raise ValueError(
                f'Engine ID {engine_id} not found or inactive. '
                f'Check MATCHMAKING_ENGINE table.')
        engine_name, class_path = row

        # Fetch all parameters for this engine
        cur.execute(
            '''SELECT param_key, param_value, param_type
               FROM   ENGINE_PARAMETER
               WHERE  engine_id = :1''',
            [engine_id]
        )
        param_rows = cur.fetchall()

    # Cast each parameter to its declared type
    params = {}
    for key, value, ptype in param_rows:
        try:
            if ptype == 'int':
                params[key] = int(value)
            elif ptype == 'float':
                params[key] = float(value)
            elif ptype == 'bool':
                params[key] = value.strip().lower() == 'true'
            else:
                params[key] = value   # string default
        except (ValueError, TypeError) as e:
            raise ValueError(
                f"ENGINE_PARAMETER cast failed for key='{key}' "
                f"value='{value}' type='{ptype}': {e}")

    return engine_name, class_path, params


def _import_class(class_path: str):
    """
    Dynamically import a class from a dotted path string.

    Example:
        'engine.mmr_engine.MMREngine'
        → imports engine.mmr_engine, returns MMREngine class

    Raises:
        ImportError if module not found.
        AttributeError if class not found in module.
    """
    module_path, class_name = class_path.rsplit('.', 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def _resolve_rating_engine(params: dict, mode_type: str):
    """
    Resolve which rating engine to use.

    Lookup order:
      1. If 'rating_engine_class' key exists in params,
         import and instantiate that class.
      2. Otherwise fall back to EloRating with mode-aware defaults.

    Rating-specific params are any params prefixed with 'rating_'
    (excluding 'rating_engine_class' itself).
    """
    rating_class_path = params.get('rating_engine_class')

    if rating_class_path:
        rating_class = _import_class(rating_class_path)

        # Collect rating-specific constructor params
        rating_params = {
            k.replace('rating_', '', 1): v
            for k, v in params.items()
            if k.startswith('rating_')
            and k != 'rating_engine_class'
        }
        return rating_class(**rating_params)

    # Default fallback: EloRating tuned per mode type
    from engine.elo_rating import EloRating
    if mode_type == 'competitive':
        return EloRating(
            k_factor=24,
            delta_cap=40,
            mode_type='competitive',
        )
    return EloRating(
        k_factor=32,
        delta_cap=50,
        mode_type='battle_royale',
    )


def load_engine(engine_id: int, mode_type: str = 'battle_royale',
                criteria=None):
    """
    Dynamically load and instantiate a matchmaking engine by ID.

    Process:
      1. Read engine_class path from MATCHMAKING_ENGINE.
      2. Read all parameters from ENGINE_PARAMETER.
      3. Resolve the nested rating engine.
      4. Dynamically import the matchmaking engine class.
      5. Instantiate with criteria, params, and rating_engine.

    Args:
        engine_id  : PK from MATCHMAKING_ENGINE table.
        mode_type  : 'battle_royale' or 'competitive'.
                     Used to set rating engine defaults.
        criteria   : MatchmakingCriteria dataclass instance.

    Returns:
        Instantiated BaseMatchmakingEngine subclass.

    Usage:
        engine = load_engine(mc.engine_id,
                             mode_type=gm.mode_type,
                             criteria=mc)
        match_id = assemble_lobby(engine, gm, session_id, region)
    """
    engine_name, class_path, params = _fetch_engine_record(engine_id)
    rating  = _resolve_rating_engine(params, mode_type)
    cls     = _import_class(class_path)

    return cls(
        criteria=criteria,
        params=params,
        rating_engine=rating,
    )


def load_engine_for_mode(mode_id: int, criteria):
    """
    Convenience loader — resolves engine from mode_id directly.
    Looks up which engine is configured for this criteria,
    then calls load_engine with the correct engine_id and mode_type.

    Args:
        mode_id  : PK from GAME_MODE table.
        criteria : MatchmakingCriteria dataclass instance.

    Returns:
        Instantiated BaseMatchmakingEngine subclass.

    Raises:
        ValueError if no engine is configured for this criteria.

    Usage:
        engine = load_engine_for_mode(gm.mode_id, mc)
    """
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            '''SELECT mc.engine_id, gm.mode_type
               FROM   MATCHMAKING_CRITERIA mc
               JOIN   GAME_MODE gm ON gm.mode_id = mc.mode_id
               WHERE  mc.criteria_id = :1''',
            [criteria.criteria_id]
        )
        row = cur.fetchone()

    if not row:
        raise ValueError(
            f'No engine configured for '
            f'criteria_id={criteria.criteria_id}. '
            f'Run engine_seed.sql and verify engine_id is set '
            f'on MATCHMAKING_CRITERIA.')

    engine_id, mode_type = row

    if engine_id is None:
        raise ValueError(
            f'engine_id is NULL on criteria_id={criteria.criteria_id}. '
            f'Run: UPDATE MATCHMAKING_CRITERIA SET engine_id=1 '
            f'WHERE criteria_id={criteria.criteria_id};')

    return load_engine(
        engine_id=int(engine_id),
        mode_type=mode_type,
        criteria=criteria,
    )