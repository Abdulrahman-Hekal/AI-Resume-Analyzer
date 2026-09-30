from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.repositories.users import UserRepository
from app.schemas.auth import UserRegisterRequest, UserLoginRequest, TokenResponse, UserResponse
from app.core.security import verify_password, create_access_token

class AuthService:
    @staticmethod
    def register(db: Session, req: UserRegisterRequest) -> TokenResponse:
        existing = UserRepository.get_by_email(db, req.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email address already exists. Please log in instead."
            )

        # Public registration always creates standard "user"
        role = "user"
        user = UserRepository.create(
            db=db,
            email=req.email,
            password=req.password,
            full_name=req.full_name,
            role=role
        )

        token = create_access_token(subject=user.id, role=user.role)
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse.model_validate(user)
        )

    @staticmethod
    def login(db: Session, req: UserLoginRequest) -> TokenResponse:
        user = UserRepository.get_by_email(db, req.email)
        if not user or not verify_password(req.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password. Please verify your credentials."
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated. Please contact support."
            )

        token = create_access_token(subject=user.id, role=user.role)
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse.model_validate(user)
        )
