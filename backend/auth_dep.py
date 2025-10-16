import os, httpx, time
from jose import jwt
from fastapi import Depends, HTTPException, status, Request
from functools import lru_cache

PROJECT_URL = os.environ.get("SUPABASE_PROJECT_URL") or os.environ.get("SUPABASE_URL")
JWKS_URL = os.environ.get("SUPABASE_JWKS_URL") or f"{PROJECT_URL}/rest/v1/rpc/jwks" if PROJECT_URL else None
AUDIENCE = "authenticated" 
ISSUER = f"{PROJECT_URL}/auth/v1" 

@lru_cache(maxsize=1)
def _get_jwks():
    r = httpx.get(JWKS_URL, timeout=10)
    r.raise_for_status()
    return r.json()

def get_current_user(request: Request):
    if not PROJECT_URL or not JWKS_URL:
        raise HTTPException(status_code=503, detail="Authentication service not configured")
        
    authorization = request.headers.get("authorization")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    jwks = _get_jwks()
    try:
        claims = jwt.decode(token, jwks, algorithms=["RS256"], audience=AUDIENCE, issuer=ISSUER, options={"verify_at_hash": False})
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="No subject in token")
    return {"id": user_id, "email": claims.get("email")}