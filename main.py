# main.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.config import Config
from dotenv import load_dotenv
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.cors import CORSMiddleware
import os
import jwt

from utils import create_jwt_token

load_dotenv()

app = FastAPI()

# Middlewares
app.add_middleware(SessionMiddleware, secret_key="une_clef_super_longue_et_secrete_pour_tester_123456")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# OAuth setup
config = Config(environ=os.environ)
oauth = OAuth(config)

# Définir explicitement l'URI de redirection
REDIRECT_URI = "http://localhost:8000/auth/google/callback"

oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile',
        'redirect_uri': REDIRECT_URI  # Spécifié explicitement
    }
)

@app.get("/")
def home():
    return RedirectResponse("/static/index.html")

@app.get("/login")
async def login(request: Request):
    # Utiliser l'URI définie explicitement
    return await oauth.google.authorize_redirect(request, REDIRECT_URI)

@app.get("/auth/google/callback")
async def auth(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
        user = token.get('userinfo')
        
        if not user:
            raise HTTPException(status_code=400, detail="Échec de la récupération des informations utilisateur")

        jwt_token = create_jwt_token({
            "email": user["email"],
            "name": user["name"]
        })

        html = f"""
        <h2>Bienvenue {user['name']}</h2>
        <p>Email : {user['email']}</p>
        <p>Ton token JWT :</p>
        <textarea rows="6" cols="80">{jwt_token}</textarea>
        <p>Utilise-le dans les appels API protégés</p>
        """
        return HTMLResponse(content=html)
    except Exception as e:
        return HTMLResponse(content=f"<h1>Erreur interne</h1><p>{str(e)}</p>", status_code=500)

@app.get("/me")
async def get_profile(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token manquant")

    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, os.getenv("JWT_SECRET"), algorithms=["HS256"])
        return {"email": payload["sub"], "name": payload["name"]}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expiré")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token invalide")