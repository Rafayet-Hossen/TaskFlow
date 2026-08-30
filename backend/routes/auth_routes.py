from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import get_db
from backend.models import User, VerificationCode, utc_now
from backend.schemas import (
    UserRegister,
    UserLogin,
    VerifyEmailRequest,
    ResendCodeRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    UserResponse,
    TokenResponse,
    MessageResponse
)
from backend.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    get_current_verified_user
)
from backend.email_service import (
    generate_pin_code,
    send_verification_email,
    send_password_reset_email
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def register_user(payload: UserRegister, db: Session = Depends(get_db)):
    email_clean = payload.email.strip().lower()
    existing_user = db.query(User).filter(User.email == email_clean).first()
    
    if existing_user and existing_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists. Please log in."
        )
    
    if existing_user and not existing_user.is_verified:
        # Update user credentials
        existing_user.full_name = payload.full_name.strip()
        existing_user.hashed_password = hash_password(payload.password)
        user = existing_user
    else:
        # Create new user
        user = User(
            email=email_clean,
            full_name=payload.full_name.strip(),
            hashed_password=hash_password(payload.password),
            is_verified=False
        )
        db.add(user)
    
    db.commit()
    db.refresh(user)

    # Invalidate previous verification codes
    db.query(VerificationCode).filter(
        VerificationCode.user_id == user.id,
        VerificationCode.purpose == "email_verification"
    ).update({"is_used": True})

    # Generate new verification PIN
    code = generate_pin_code()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.VERIFICATION_CODE_EXPIRE_MINUTES)
    
    verification_entry = VerificationCode(
        user_id=user.id,
        code=code,
        purpose="email_verification",
        expires_at=expires_at,
        is_used=False
    )
    db.add(verification_entry)
    db.commit()

    # Send verification email asynchronously
    await send_verification_email(user.email, user.full_name, code)

    return MessageResponse(
        message="Registration successful! A 6-digit verification code has been sent to your email.",
        success=True
    )

@router.post("/verify-email", response_model=TokenResponse)
async def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)):
    email_clean = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email_clean).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account associated with this email address."
        )
    
    # Check valid code
    now = datetime.now(timezone.utc)
    valid_code = db.query(VerificationCode).filter(
        VerificationCode.user_id == user.id,
        VerificationCode.purpose == "email_verification",
        VerificationCode.code == payload.code.strip(),
        VerificationCode.is_used == False,
        VerificationCode.expires_at > now
    ).first()

    if not valid_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code. Please request a new one."
        )

    # Mark verified
    valid_code.is_used = True
    user.is_verified = True
    db.commit()
    db.refresh(user)

    # Issue access token for instant login
    access_token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )

@router.post("/resend-code", response_model=MessageResponse)
async def resend_verification_code(payload: ResendCodeRequest, db: Session = Depends(get_db)):
    email_clean = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email_clean).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found.")
    
    if user.is_verified:
        return MessageResponse(message="Your email is already verified. You can log in directly.", success=True)

    # Invalidate previous codes
    db.query(VerificationCode).filter(
        VerificationCode.user_id == user.id,
        VerificationCode.purpose == "email_verification"
    ).update({"is_used": True})

    code = generate_pin_code()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.VERIFICATION_CODE_EXPIRE_MINUTES)
    
    verification_entry = VerificationCode(
        user_id=user.id,
        code=code,
        purpose="email_verification",
        expires_at=expires_at,
        is_used=False
    )
    db.add(verification_entry)
    db.commit()

    await send_verification_email(user.email, user.full_name, code)

    return MessageResponse(
        message="A new 6-digit verification code has been dispatched to your email.",
        success=True
    )

@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin, db: Session = Depends(get_db)):
    email_clean = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email_clean).first()
    
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password. Please try again."
        )

    if not user.is_verified:
        # Resend code automatically to assist user
        code = generate_pin_code()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.VERIFICATION_CODE_EXPIRE_MINUTES)
        verification_entry = VerificationCode(
            user_id=user.id,
            code=code,
            purpose="email_verification",
            expires_at=expires_at,
            is_used=False
        )
        db.add(verification_entry)
        db.commit()
        await send_verification_email(user.email, user.full_name, code)

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your email has not been verified yet. We have sent a verification code to your email."
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )

@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    email_clean = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email_clean).first()
    
    if user:
        # Invalidate old reset codes
        db.query(VerificationCode).filter(
            VerificationCode.user_id == user.id,
            VerificationCode.purpose == "password_reset"
        ).update({"is_used": True})

        code = generate_pin_code()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.VERIFICATION_CODE_EXPIRE_MINUTES)
        
        reset_entry = VerificationCode(
            user_id=user.id,
            code=code,
            purpose="password_reset",
            expires_at=expires_at,
            is_used=False
        )
        db.add(reset_entry)
        db.commit()

        await send_password_reset_email(user.email, user.full_name, code)

    return MessageResponse(
        message="If that email is registered with us, a password reset code has been sent.",
        success=True
    )

@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    email_clean = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email_clean).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request or code."
        )

    now = datetime.now(timezone.utc)
    valid_code = db.query(VerificationCode).filter(
        VerificationCode.user_id == user.id,
        VerificationCode.purpose == "password_reset",
        VerificationCode.code == payload.code.strip(),
        VerificationCode.is_used == False,
        VerificationCode.expires_at > now
    ).first()

    if not valid_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset code. Please request a new one."
        )

    # Reset password
    valid_code.is_used = True
    user.hashed_password = hash_password(payload.new_password)
    db.commit()

    return MessageResponse(
        message="Your password has been successfully reset. You can now log in with your new password.",
        success=True
    )

@router.get("/me", response_model=UserResponse)
async def get_my_profile(current_user: User = Depends(get_current_verified_user)):
    return UserResponse.model_validate(current_user)

