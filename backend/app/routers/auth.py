from fastapi import APIRouter, Depends, Header, HTTPException, status
import requests
from sqlalchemy.orm import Session

from ..core.config import settings
from ..database import get_db
from ..dependencies.auth import create_session, get_current_user, hash_password, revoke_current_session, verify_password
from ..models import User
from ..schemas import AuthIn, AuthOut, OAuthIn, SignupIn, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])

GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"


def verify_google_credential(credential: str) -> dict:
    if not settings.google_client_id:
        raise HTTPException(status_code=500, detail="Google OAuth is not configured on the backend")

    try:
        response = requests.get(GOOGLE_TOKENINFO_URL, params={"id_token": credential}, timeout=10)
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail="Could not contact Google OAuth verification service") from exc

    if response.status_code != 200:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google credential")

    profile = response.json()
    if profile.get("aud") != settings.google_client_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Google credential audience mismatch")
    if profile.get("email_verified") not in (True, "true", "True", "1"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Google email is not verified")
    if not profile.get("email") or not profile.get("sub"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Google credential is missing account details")
    return profile


@router.post("/signup", response_model=AuthOut)
def signup(payload: SignupIn, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        name=payload.name.strip(),
        email=email,
        phone=payload.phone.strip(),
        role="buyer",
        password_hash=hash_password(payload.password),
        is_active=True,
        seller_status="APPROVED",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"user": user, "token": create_session(db, user)}


@router.post("/login", response_model=AuthOut)
def login(payload: AuthIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.strip().lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")
    return {"user": user, "token": create_session(db, user)}


@router.post("/oauth", response_model=AuthOut)
def oauth(payload: OAuthIn, db: Session = Depends(get_db)):
    if payload.provider != "google":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only Google OAuth is supported")

    profile = verify_google_credential(payload.credential)
    email = profile["email"].strip().lower()
    google_sub = profile["sub"]
    name = (profile.get("name") or email.split("@")[0]).strip()

    user = db.query(User).filter(User.google_sub == google_sub).first()
    if not user:
        user = db.query(User).filter(User.email == email).first()

    if user and not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")

    if not user:
        user = User(
            name=name,
            email=email,
            phone="9999999999",
            role=payload.role,
            password_hash="",
            oauth_provider="google",
            google_sub=google_sub,
            is_active=True,
            seller_status="PENDING" if payload.role == "seller" else "APPROVED",
            store_name=f"{name}'s Store" if payload.role == "seller" else "",
        )
        db.add(user)
    else:
        user.name = user.name or name
        user.oauth_provider = "google"
        user.google_sub = google_sub
        if user.role != "admin":
            user.role = payload.role
            if payload.role == "seller" and user.seller_status not in {"APPROVED", "SUSPENDED"}:
                user.seller_status = "PENDING"
            elif payload.role == "buyer" and not user.seller_status:
                user.seller_status = "APPROVED"
            if payload.role == "seller" and not user.store_name:
                user.store_name = f"{user.name}'s Store"

    db.commit()
    db.refresh(user)
    return {"user": user, "token": create_session(db, user)}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/logout")
def logout(authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    revoke_current_session(authorization, db)
    return {"status": "ok"}
