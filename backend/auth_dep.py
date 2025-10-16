import os, httpx, time
from jose import jwt
from fastapi import Depends, HTTPException, status, Request
from functools import lru_cache

PROJECT_URL = os.environ.get("SUPABASE_PROJECT_URL") or os.environ.get("SUPABASE_URL")
JWKS_URL = os.environ.get("SUPABASE_JWKS_URL") or f"{PROJECT_URL}/auth/v1/jwks" if PROJECT_URL else None
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
    print(f"Debug: Received token: {token[:50]}...")  # Log first 50 chars
    print(f"Debug: JWKS_URL: {JWKS_URL}")
    
    try:
        jwks = _get_jwks()
        print(f"Debug: JWKS retrieved successfully")
    except Exception as e:
        print(f"Debug: JWKS error: {e}")
        raise HTTPException(status_code=401, detail=f"JWKS error: {str(e)}")
    
    try:
        claims = jwt.decode(token, jwks, algorithms=["RS256"], audience=AUDIENCE, issuer=ISSUER, options={"verify_at_hash": False})
        print(f"Debug: Token decoded successfully")
    except Exception as e:
        print(f"Debug: Token decode error: {e}")
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="No subject in token")
    
    print(f"Debug: User authenticated: {user_id}")
    return {"id": user_id, "email": claims.get("email")}