from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr, Field
from supabase import create_client, Client
from typing import Optional
import os
from auth_dep import get_current_user

# Initialize Supabase client
supabase_url = os.environ.get("SUPABASE_PROJECT_URL")
supabase_key = os.environ.get("SUPABASE_ANON_KEY")

if not supabase_url or not supabase_key:
    print("Warning: Supabase configuration missing. Authentication endpoints will not work.")
    supabase = None
else:
    supabase: Client = create_client(supabase_url, supabase_key)

router = APIRouter(prefix="/auth", tags=["authentication"])

# Pydantic models for request/response
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: dict
    message: str

class MessageResponse(BaseModel):
    message: str

@router.post("/register", response_model=AuthResponse)
async def register(user_data: UserRegister):
    """Register a new user"""
    if supabase is None:
        raise HTTPException(status_code=503, detail="Authentication service not configured")
    try:
        # Create user with Supabase Auth
        response = supabase.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password,
            "options": {
                "data": {
                    "full_name": user_data.full_name
                }
            }
        })
        
        if response.user is None:
            raise HTTPException(
                status_code=400,
                detail="Registration failed. Email may already be registered."
            )
        
        return AuthResponse(
            access_token=response.session.access_token,
            refresh_token=response.session.refresh_token,
            user={
                "id": response.user.id,
                "email": response.user.email,
                "full_name": user_data.full_name
            },
            message="Registration successful. Please check your email to verify your account."
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/login", response_model=AuthResponse)
async def login(user_credentials: UserLogin):
    """Login user"""
    if supabase is None:
        raise HTTPException(status_code=503, detail="Authentication service not configured")
    try:
        response = supabase.auth.sign_in_with_password({
            "email": user_credentials.email,
            "password": user_credentials.password
        })
        
        if response.user is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
        
        return AuthResponse(
            access_token=response.session.access_token,
            refresh_token=response.session.refresh_token,
            user={
                "id": response.user.id,
                "email": response.user.email,
                "full_name": response.user.user_metadata.get("full_name")
            },
            message="Login successful"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Login failed: {str(e)}"
        )

@router.post("/logout", response_model=MessageResponse)
async def logout(authorization: str = Header(None)):
    """Logout user"""
    try:
        if authorization and authorization.startswith("Bearer "):
            token = authorization.split(" ", 1)[1]
            # Set the session token for logout
            supabase.auth.set_session(token, "")
            
        response = supabase.auth.sign_out()
        
        return MessageResponse(message="Logout successful")
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Logout failed: {str(e)}"
        )

class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh token")

@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(token_data: RefreshTokenRequest):
    """Refresh access token"""
    try:
        response = supabase.auth.refresh_session(token_data.refresh_token)
        
        if response.session is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid refresh token"
            )
        
        return AuthResponse(
            access_token=response.session.access_token,
            refresh_token=response.session.refresh_token,
            user={
                "id": response.user.id,
                "email": response.user.email,
                "full_name": response.user.user_metadata.get("full_name")
            },
            message="Token refreshed successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Token refresh failed: {str(e)}"
        )

@router.get("/me")
async def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    """Get current user profile"""
    try:
        # Get user details from Supabase
        user_response = supabase.auth.get_user()
        
        if user_response.user is None:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
        
        return {
            "id": user_response.user.id,
            "email": user_response.user.email,
            "full_name": user_response.user.user_metadata.get("full_name"),
            "email_verified": user_response.user.email_confirmed_at is not None,
            "created_at": user_response.user.created_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get user profile: {str(e)}"
        )

class ResetPasswordRequest(BaseModel):
    email: EmailStr

@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(reset_data: ResetPasswordRequest):
    """Send password reset email"""
    try:
        response = supabase.auth.reset_password_email(reset_data.email)
        
        return MessageResponse(
            message="If an account with this email exists, a password reset link has been sent."
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Password reset failed: {str(e)}"
        )

class VerifyEmailRequest(BaseModel):
    email: EmailStr

@router.post("/verify-email", response_model=MessageResponse)
async def resend_verification(verify_data: VerifyEmailRequest):
    """Resend email verification"""
    try:
        response = supabase.auth.resend({
            "type": "signup",
            "email": verify_data.email
        })
        
        return MessageResponse(
            message="Verification email sent successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to send verification email: {str(e)}"
        )
