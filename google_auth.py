from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from authlib.integrations.starlette_client import OAuth
import os
from utils import create_jwt_token

router = APIRouter()

oauth = OAuth()
oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

GOOGLE_REDIRECT_URI = "http://localhost:8000/auth/google/callback"

@router.get("/login/google")
async def login_google(request: Request):
    return await oauth.google.authorize_redirect(request, GOOGLE_REDIRECT_URI)

@router.get("/auth/google/callback")
async def auth_google(request: Request):
    token = await oauth.google.authorize_access_token(request)
    user = token.get('userinfo')
    if not user:
        raise HTTPException(status_code=400, detail="Google auth failed")

    jwt_token = create_jwt_token({
        "email": user["email"],
        "name": user["name"]
    })

    html = f"""
    <h2>Google login successful! Welcome {user['name']}</h2>
    <p>Email: {user['email']}</p>
    <p>Your JWT token:</p>
    <textarea rows="6" cols="80">{jwt_token}</textarea>
    """
    return HTMLResponse(content=html)