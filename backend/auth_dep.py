import os
from jose import jwt
from fastapi import Depends, HTTPException, status, Request

PROJECT_URL = os.environ.get("SUPABASE_PROJECT_URL") or os.environ.get("SUPABASE_URL")
JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET") or os.environ.get("SUPABASE_KEY")
AUDIENCE = "authenticated" 
ISSUER = f"{PROJECT_URL}/auth/v1" if PROJECT_URL else None

def get_current_user(request: Request):
    if not PROJECT_URL or not JWT_SECRET:
        raise HTTPException(status_code=503, detail="Authentication service not configured")
        
    authorization = request.headers.get("authorization")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    
    token = authorization.split(" ", 1)[1]
    print(f"Debug: Received token: {token[:50]}...")
    print(f"Debug: Using JWT_SECRET validation")
    
    try:
        # Supabase uses HS256 with the anon/service key as secret
        claims = jwt.decode(
            token, 
            JWT_SECRET, 
            algorithms=["HS256"], 
            audience=AUDIENCE, 
            issuer=ISSUER,
            options={"verify_aud": False, "verify_iss": False}  # Be more lenient for debugging
        )
        print(f"Debug: Token decoded successfully")
    except Exception as e:
        print(f"Debug: Token decode error: {e}")
        # Try without audience/issuer validation
        try:
            claims = jwt.decode(token, JWT_SECRET, algorithms=["HS256"], options={"verify_aud": False, "verify_iss": False})
            print(f"Debug: Token decoded with relaxed validation")
        except Exception as e2:
            print(f"Debug: Relaxed decode also failed: {e2}")
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="No subject in token")
    
    print(f"Debug: User authenticated: {user_id}")
    return {"id": user_id, "email": claims.get("email")}