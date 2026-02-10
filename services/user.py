from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.exceptions import ErrorCode, ValidationError
from app.db.models import User

    
async def validate_email_uniqueness(email: str, session: AsyncSession):
    result = await session.exec(
        select(User).where(User.email == email)
    )
    if result.first():
        raise ValidationError(
            error_code=ErrorCode.DUPLICATE_ENTRY.value,
            message="Someone else is using this email."
        )
        