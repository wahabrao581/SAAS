from fastapi import FastAPI

from router import router
from contextlib import asynccontextmanager
from db_config import TORTOISE_ORM, connect_db, disconnect_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await disconnect_db()

app = FastAPI(lifespan=lifespan)
app.include_router(router)
