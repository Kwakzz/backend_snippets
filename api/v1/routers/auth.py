from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlmodel import select
from sqlalchemy.orm import joinedload
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.exc import IntegrityError
from app.core.exceptions import AuthenticationFailedError, InternalServerError, ResourceNotFoundError,  ValidationError, ErrorCode
from app.schemas.user import ClassCodeLoginResponse, EmailSuccess, SendEmailSchema, UserResponse
from app.schemas.auth import ClassCodeLogin, EmailPasswordCreds, GoogleUser, VerifyTokenSchema, ChangePasswordSchema, SSOProvider
from app.db.session import get_session
from app.core.security import create_access_token, create_passwordless_login_token, get_password_hash, verify_password
from app.db.models import Classroom, User, UserSSO
from app.core.logging import logger
from app.services.auth import get_user_from_access_token, verify_google_token, get_user_from_passwordless_login_token
from app.services.email import send_email
from app.core.config import settings


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register")
async def register(
    user_data: EmailPasswordCreds, 
    session: AsyncSession = Depends(get_session)
) -> UserResponse:
    
    """Create a user instance with an email and password.

    Args:
        user_data (UserCreate): Email and password.
        session (AsyncSession, optional): Database async session. Defaults to Depends(get_session).

    Raises:
        DuplicateEntry: Raised when duplicate email is used.
        InternalServerError: For unexpected errors.

    Returns:
        UserResponse: A User schema
    """
    try:

        new_user = User(
            email=user_data.email, 
            password=get_password_hash(user_data.password)
        )
        
        session.add(new_user)
        await session.commit()
        
        jwt = create_access_token(
            user_id=new_user.id,
            token_version=new_user.jwt_version
        )
        
        return UserResponse (
            id=new_user.id,
            email=new_user.email,
            token=jwt,
            created_at=str(new_user.created_at)
        )  
        
    except IntegrityError as e:
        await session.rollback()
        raise ValidationError(
            error_code=ErrorCode.DUPLICATE_ENTRY.value,
            message="This email is already registered with Wonderspaced."
        )
        
    except Exception as e:
        logger.error("Error registering user: {}", str(e), exc_info=True)
        raise InternalServerError()
    

@router.post('/password-login')
async def password_login(
    user_data: EmailPasswordCreds,
    session: AsyncSession = Depends(get_session)
) -> UserResponse:
    
    """
    Returns a token for making authenticated requests.

    Args:
        user_data (UserCreate): Email and password.
        session (AsyncSession, optional): Asynchronous database session. Defaults to Depends(get_session).

    Raises:
        ValidationError: Raised when either the email or password is wrong.
        InternalServerError: An unexpected error occurs.

    Returns:
        UserResponse: User details.
    """  
    try:
        
        result = await session.exec(
            select(User)
            .where(User.email == user_data.email)
        )
        user = result.one_or_none()
        if not user:
            raise ValidationError(
                error_code=ErrorCode.UNREGISTERED_EMAIL.value,
                message="Email hasn't been registered with us. Perhaps you want to sign up?"
            )
            
        if not verify_password(user_data.password, user.password):
            raise ValidationError(
                error_code=ErrorCode.WRONG_PASSWORD.value,
                message="Wrong password. Please try again."
            )

        user.last_login = datetime.now()
        user.last_active = datetime.now()
            
        jwt = create_access_token(
            user_id=user.id,
            token_version=user.jwt_version
        )
        
        await session.commit()    

        return UserResponse(
            id=user.id,
            email=user.email,
            token=jwt,
            created_at=str(user.created_at),
            email_verified_at=str(user.email_verified_at) if user.email_verified_at else None,
            first_name=user.first_name,
            last_name=user.last_name,
            school=user.school,
            is_family_account=user.is_family_account,
            is_teacher_account=user.is_teacher_account
        )

    except ValidationError as e:
        logger.error("Validation error: {}", str(e), exc_info=True)
        raise
    
    except Exception as e:
        logger.error(f"Error logging in: {str(e)}", exc_info=True)
        raise InternalServerError()
    
    
@router.post("/class-code-login")
async def class_code_login(
    req: ClassCodeLogin,
    session: AsyncSession = Depends(get_session)
) -> ClassCodeLoginResponse:
    
    try:
        classroom_result = await session.exec(
            select(Classroom)
            .where(Classroom.code == req.class_code)
            .options(joinedload(Classroom.user))
        )
        classroom = classroom_result.first()
        if not classroom:
            raise ResourceNotFoundError(message="No class has this code. Ask your teacher and try again.")
        
        jwt = create_access_token(
            user_id=classroom.user.id,
            token_version=classroom.user.jwt_version
        )
        
        teacher_name = f"{classroom.user.first_name} {classroom.user.last_name}"
        
        return ClassCodeLoginResponse(
            token=jwt,
            class_code=classroom.code,
            class_id=classroom.id,
            class_name=classroom.name,
            teacher_name=teacher_name
        )
        
    except ResourceNotFoundError as e:
        raise
        
    except Exception as e:
        logger.error("Error logging in with class code: {}", str(e), exc_info=True)
        raise InternalServerError()
    
    
@router.post("/google")
async def google_auth(
    google_user: GoogleUser,
    session: AsyncSession = Depends(get_session)
) -> UserResponse:
    
    """User sends ID token from client. ID token is used to get user's email and google ID. If email is associated with an existing user, log them in, otherwise create an account. If user doesn't have an UserSSO instance for storing their Google ID, create one.

    Args:
        google_user (GoogleUser): Contains ID token for authenticating Google user.
        session (AsyncSession, optional): Asynchronous database session. Defaults to Depends(get_session).

    Raises:
        InternalServerError: For unexpected errors

    Returns:
        UserResponse: A User schema.
    """
    try:
        user_info = verify_google_token(google_user.id_token)

        email = user_info["email"]
        google_id = user_info["sub"]  # Google's unique user ID
        
        is_new = False

        # Check if a user with this email exists
        result = await session.exec(
            select(User).where(
                User.email == email
            )
        )
        user = result.first()

        if user:
            user.last_login = datetime.now()
            user.last_active = datetime.now()
            if not user.email_verified_at:
                user.email_verified_at = datetime.now()
            
            # Check if this user already has a linked Google account
            sso_result = await session.exec(
                select(UserSSO).where(
                    UserSSO.provider == SSOProvider.GOOGLE.value, 
                    UserSSO.provider_id == google_id,
                    UserSSO.user_id == user.id
                )
            )
            user_sso = sso_result.first()

            if not user_sso:
                # If Google account is not linked, link it
                user_sso = UserSSO(
                    user_id=user.id, 
                    provider=SSOProvider.GOOGLE.value, 
                    provider_id=google_id
                )
                session.add(user_sso)

        else:
            is_new = True
            
            # Create new user and link Google account
            user = User(
                email=email,
                email_verified_at=datetime.now()
            )
            session.add(user)
            await session.flush()  # Ensures user.id is available

            user_sso = UserSSO(
                user_id=user.id, 
                provider=SSOProvider.GOOGLE.value, 
                provider_id=google_id
            )
            session.add(user_sso)
            
        await session.commit()
        
        jwt = create_access_token(
            user_id=user.id,
            token_version=user.jwt_version
        )

        return UserResponse(
            id=user.id,
            email=user.email,
            token=jwt,
            created_at=str(user.created_at),
            email_verified_at=str(user.email_verified_at) if user.email_verified_at else None,
            is_new=is_new,
            first_name=user.first_name,
            last_name=user.last_name,
            school=user.school,
            is_family_account=user.is_family_account,
            is_teacher_account=user.is_teacher_account
        ) 
        
    except AuthenticationFailedError as e:
        logger.error("Authentication failed: {}", str(e), exc_info=True)
        raise 
    
    except Exception as e:
        logger.error("Error authenticating with Google: {}", str(e), exc_info=True)
        raise InternalServerError()
    
    
@router.post('/request-passwordless-login')
async def send_login_link(
    login_request: SendEmailSchema,
    session: AsyncSession = Depends(get_session)
) -> EmailSuccess:
    
    try:    
        email = login_request.email
        result = await session.exec(
            select(User).where(User.email == email)
        )
        user = result.one_or_none()
        if not user:
            raise ValidationError(
                error_code=ErrorCode.UNREGISTERED_EMAIL.value,
                message="Email hasn't been registered with us. Perhaps you want to sign up?"
            )
            
        token = create_passwordless_login_token(
            email=email, 
            expires_delta=timedelta(minutes=30)
        )
        
        magic_link = f"https://wspaced-api-{settings.ENV.lower()}-261447173455.us-central1.run.app/api/v1/login-link?token={token}"
        body_html = f"""
        <p>Hi there,<p>
        <p>You're receiving this email because you requested a passwordless login. Tap the link below to log in without a password:</p>
        <a href="{magic_link}" style="color: blue; text-decoration: none;">Login without password</a>
        <p>Once you log in, you can change your password in Settings. The link expires in 30 minutes.</p>
        <p>Stay wonderful,</p>
        <p>The Wonderspaced Team.</p>
        """
        
        send_email(
            to_email=email,
            subject="Passwordless Login",
            body_html=body_html
        )
        
        return EmailSuccess(
            message="Check your email for a login link."
        )
        
    except ValidationError as e:
        logger.error("User with email not found or missing field: {}", str(e), exc_info=True)
        raise
    
    except Exception as e:
        logger.error("Error requesting passwordless login: {}", str(e), exc_info=True)
        raise InternalServerError()
        
        
@router.post('/verify-passwordless-login')
async def verify_passwordless_login(
    verify_request: VerifyTokenSchema,
    session: AsyncSession = Depends(get_session)
) -> UserResponse:
    
    try:    
        token = verify_request.token
        user = await get_user_from_passwordless_login_token(
            token=token,
            session=session
        )
            
        user.last_login = datetime.now()
        user.last_active = datetime.now()
        if not user.email_verified_at:
            user.email_verified_at = datetime.now()
        
        await session.commit()
        
        jwt = create_access_token(
            user_id=user.id,
            token_version=user.jwt_version
        )        

        return UserResponse(
            id=user.id,
            email=user.email,
            token=jwt,
            created_at=str(user.created_at),
            email_verified_at=str(user.email_verified_at) if user.email_verified_at else None,
            first_name=user.first_name,
            last_name=user.last_name,
            school=user.school,
            is_family_account=user.is_family_account,
            is_teacher_account=user.is_teacher_account
        )
        
    except AuthenticationFailedError as e:
        logger.error("Authentication failed: {}", str(e), exc_info=True)    
        raise
    
    except Exception as e:
        logger.error("Error verifying passwordless login: {}", str(e), exc_info=True)
        raise InternalServerError()


@router.post('/change-password')
async def change_password(
    passwords: ChangePasswordSchema,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_user_from_access_token)  
) -> UserResponse:
    
    try:
        if passwords.password1 != passwords.password2:
            raise ValidationError(
                error_code=ErrorCode.VALUES_DONT_MATCH.value,
                message="Passwords don't match"
            )
            
        user.password = get_password_hash(passwords.password1)
        user.jwt_version = user.jwt_version + 1
        session.add(user)
        await session.commit()
        
        return UserResponse(
            id=user.id,
            email=user.email
        )
        
    except ValidationError as e:
        logger.error("Validation error: {}", str(e), exc_info=True)    
        raise
    
    except Exception as e:
        logger.error("Error changing password: {}", str(e), exc_info=True)
        raise InternalServerError()
    

@router.post('/request-email-verification')
async def request_email_verification(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_user_from_access_token)  
) -> EmailSuccess:
    
    try:
        if user.email_verified_at:
            raise ValidationError(
                error_code=ErrorCode.ALREADY_VERIFIED.value,
                message="Email already verified."
            )
            
        token = create_access_token(
            user_id=user.id, 
            token_version=user.jwt_version,
            expires_delta=timedelta(hours=24)
        )
        magic_link = f"https://wspaced-api-{settings.ENV.lower()}-261447173455.us-central1.run.app/api/v1/verify-email-link?token={token}"
        body_html = f"""
        <p>Hi there,<p>
        <p>Tap the link below to verify your email:</p>
        <a href="{magic_link}" style="color: blue; text-decoration: none;">Verify Email</a>
        <p>The link expires in 24 hours.</p>
        <p>Stay wonderful,</p>
        <p>The Wonderspaced Team.</p>
        """
        
        send_email(
            to_email=user.email,
            subject="Email Verification",
            body_html=body_html
        )
        
        return EmailSuccess(
            message="Check your email for a verification link."
        )
        
    except ValidationError as e:
        logger.error("Validation error: {}", str(e), exc_info=True)
        raise
    
    except Exception as e:
        logger.error("Error requesting email verification: {}", str(e), exc_info=True)
        raise InternalServerError()
    
    
@router.post('/verify-email')
async def verify_email(
    verify_request: VerifyTokenSchema,
    session: AsyncSession = Depends(get_session)
) -> UserResponse:
    
    try:    
        token = verify_request.token
        user = await get_user_from_access_token(
            token=token,
            session=session
        )
        
        if user.email_verified_at:
            raise ValidationError(
                error_code=ErrorCode.ALREADY_VERIFIED.value,
                message="Email already verified."
            )
            
        user.email_verified_at = datetime.now()
        session.add(user)  
        await session.commit()  
        
        return UserResponse(
            id=user.id,
            email=user.email,
            email_verified_at=str(user.email_verified_at)
        )
        
    except ValidationError as e:
        logger.error("Email already verified: {}", str(e), exc_info=True)
        raise
    
    except AuthenticationFailedError as e:
        logger.error("Authentication failed: {}", str(e), exc_info=True)    
        raise
    
    except Exception as e:
        logger.error("Error verifying email: {}", str(e), exc_info=True)
        raise InternalServerError()