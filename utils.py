# utils.py
import jwt
from datetime import datetime, timedelta

JWT_SECRET = "b43663ab9453ce164466f0c7f5e8b9c6566ca42ed28448d5de41c195045eae77"

def create_jwt_token(user_data: dict) -> str:
    payload = {
        "sub": user_data["email"],
        "name": user_data["name"],
        "exp": datetime.utcnow() + timedelta(hours=1),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return token
