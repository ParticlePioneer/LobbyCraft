from contextlib import asynccontextmanager 
from fastapi import FastAPI 
from fastapi.responses import RedirectResponse
from db.connection import init_pool, close_pool 
from api import players, parties, queue, matches 
@asynccontextmanager 
async def lifespan(app: FastAPI): 
    init_pool() 
    yield 
    close_pool() 
app = FastAPI(title='Matchmaking API', version='1.0.0', lifespan=lifespan) 
app.include_router(players.router, prefix='/players', tags=['players']) 
app.include_router(parties.router, prefix='/parties', tags=['parties']) 
app.include_router(queue.router,   
prefix='/queue',   tags=['queue']) 
app.include_router(matches.router, prefix='/matches', tags=['matches']) 

@app.get("/", include_in_schema=False)
def read_root():
    return RedirectResponse(url="/docs")