from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET", "5zD9mkpSQmjQxtZRRYU14TIcUVPUZY6gVmJxbeyCboE"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from google_auth import router as google_router
from facebook_auth import router as facebook_router

from database import database
from models import metadata
import sqlalchemy

@app.on_event("startup")
async def startup():
    await database.connect()
    engine = sqlalchemy.create_engine(os.getenv("DATABASE_URL"))
    metadata.create_all(engine)

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

app.include_router(google_router)
app.include_router(facebook_router)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return RedirectResponse("/static/index.html")