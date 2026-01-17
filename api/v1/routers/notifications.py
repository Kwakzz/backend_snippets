from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.exceptions import InternalServerError
from app.schemas.notifications import DeviceToken
from app.db.session import get_session
from app.db.models import User
from app.core.logging import logger
from app.services.auth import get_user_from_access_token
from firebase_admin import messaging
from app.utils.notifications import NotificationTopic


router = APIRouter(prefix="/notifications", tags=["Notifications"])

        
@router.post('/send-device-token')
async def get_device_token(
    request: DeviceToken,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_user_from_access_token)  
):
    try:
        
        user.device_token = request.token 
        
        session.add(user)
        await session.commit() 

        messaging.subscribe_to_topic(
            tokens=[request.token],
            topic=NotificationTopic.ALL_USERS.value
        )

        return DeviceToken(
            token=request.token
        )
    
    except Exception as e:
        logger.error("Error getting device token: {}", str(e), exc_info=True)
        raise InternalServerError()