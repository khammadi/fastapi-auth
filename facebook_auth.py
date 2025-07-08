from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from authlib.integrations.starlette_client import OAuth
import os
from utils import create_jwt_token

router = APIRouter()

oauth = OAuth()
oauth.register(
    name='facebook',
    client_id=os.getenv("FACEBOOK_CLIENT_ID"),
    client_secret=os.getenv("FACEBOOK_CLIENT_SECRET"),
    access_token_url='https://graph.facebook.com/v12.0/oauth/access_token',
    authorize_url='https://www.facebook.com/v12.0/dialog/oauth',
    api_base_url='https://graph.facebook.com/v12.0/',
    client_kwargs={'scope': 'email public_profile'}
)

FACEBOOK_REDIRECT_URI = "http://localhost:8000/auth/facebook/callback"

@router.get("/login/facebook")
async def login_facebook(request: Request):
    return await oauth.facebook.authorize_redirect(request, FACEBOOK_REDIRECT_URI)

@router.get("/auth/facebook/callback")
async def auth_facebook(request: Request):
    token = await oauth.facebook.authorize_access_token(request)
    resp = await oauth.facebook.get('me?fields=id,name,email', token=token)
    user = resp.json()
    if 'error' in user:
        raise HTTPException(status_code=400, detail="Facebook auth failed")

    jwt_token = create_jwt_token({
        "email": user.get("email", ""),
        "name": user["name"]
    })

    html = f"""
    <h2>Facebook login successful! Welcome {user['name']}</h2>
    <p>Email: {user.get('email', 'No email provided')}</p>
    <p>Your JWT token:</p>
    <textarea rows="6" cols="80">{jwt_token}</textarea>
    """
    return HTMLResponse(content=html)
