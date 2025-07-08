from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

# Middleware session (clé secrète depuis .env ou valeur par défaut)
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET", "default_secret_key"))

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En prod, mettre l'URL de ton frontend ici
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import des routers (assure-toi que google_auth.py et facebook_auth.py existent et exportent un router)
from google_auth import router as google_router
from facebook_auth import router as facebook_router

app.include_router(google_router)
app.include_router(facebook_router)

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Route racine qui redirige vers index.html dans /static
@app.get("/")
async def root():
    return RedirectResponse("/static/index.html")
