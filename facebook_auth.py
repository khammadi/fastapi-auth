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
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET", "default_secret_key"))
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

# Définir explicitement les URIs de redirection
GOOGLE_REDIRECT_URI = "http://localhost:8000/auth/google/callback"
FACEBOOK_REDIRECT_URI = "http://localhost:8000/auth/facebook/callback"

# Configuration Google
oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile',
        'redirect_uri': GOOGLE_REDIRECT_URI
    }
)

# Configuration Facebook
oauth.register(
    name='facebook',
    client_id=os.getenv("FACEBOOK_CLIENT_ID"),
    client_secret=os.getenv("FACEBOOK_CLIENT_SECRET"),
    access_token_url='https://graph.facebook.com/v12.0/oauth/access_token',
    authorize_url='https://www.facebook.com/v12.0/dialog/oauth',
    api_base_url='https://graph.facebook.com/v12.0/',
    client_kwargs={
        'scope': 'email public_profile',
        'redirect_uri': FACEBOOK_REDIRECT_URI
    }
)

@app.get("/")
def home():
    return RedirectResponse("/static/index.html")

# Routes Google
@app.get("/login/google")
async def login_google(request: Request):
    return await oauth.google.authorize_redirect(request, GOOGLE_REDIRECT_URI)

@app.get("/auth/google/callback")
async def auth_google(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
        user = token.get('userinfo')
        
        if not user:
            raise HTTPException(status_code=400, detail="Failed to get user info from Google")
        
        jwt_token = create_jwt_token({
            "email": user["email"],
            "name": user["name"]
        })

        return HTMLResponse(content=f"""
            <h2>Google Login Successful</h2>
            <p>Welcome {user['name']}</p>
            <p>Email: {user['email']}</p>
            <p>JWT Token:</p>
            <textarea rows="6" cols="80">{jwt_token}</textarea>
        """)
    except Exception as e:
        return HTMLResponse(content=f"<h1>Google Login Error</h1><p>{str(e)}</p>", status_code=500)

# Routes Facebook
@app.get("/login/facebook")
async def login_facebook(request: Request):
    return await oauth.facebook.authorize_redirect(request, FACEBOOK_REDIRECT_URI)

@app.get("/auth/facebook/callback")
async def auth_facebook(request: Request):
    try:
        token = await oauth.facebook.authorize_access_token(request)
        
        # Récupérer les infos utilisateur
        resp = await oauth.facebook.get('me?fields=id,name,email', token=token)
        user = resp.json()
        
        if 'error' in user:
            raise HTTPException(status_code=400, detail="Failed to get user info from Facebook")
        
        jwt_token = create_jwt_token({
            "email": user.get("email", ""),
            "name": user["name"]
        })

        return HTMLResponse(content=f"""
            <h2>Facebook Login Successful</h2>
            <p>Welcome {user['name']}</p>
            <p>Email: {user.get('email', 'No email provided')}</p>
            <p>JWT Token:</p>
            <textarea rows="6" cols="80">{jwt_token}</textarea>
        """)
    except Exception as e:
        return HTMLResponse(content=f"<h1>Facebook Login Error</h1><p>{str(e)}</p>", status_code=500)

# Route protégée commune
@app.get("/me")
async def get_profile(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")

    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, os.getenv("JWT_SECRET"), algorithms=["HS256"])
        return {"email": payload["sub"], "name": payload["name"]}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")