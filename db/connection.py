import oracledb 
from config import settings 
 
_pool = None 
 
def init_pool(): 
    global _pool 
    _pool = oracledb.create_pool( 
        user=settings.oracle_user, 
        password=settings.oracle_password, 
        dsn=settings.oracle_dsn, 
        min=2, max=10, increment=1, 
    ) 
 
def get_conn(): 
    if _pool is None: 
        raise RuntimeError('Pool not initialised') 
    return _pool.acquire() 
 
def close_pool(): 
    if _pool: 
        _pool.close() 