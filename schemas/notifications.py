from pydantic import BaseModel


class DeviceToken(BaseModel):
    token: str
    
    
class PushNotification(BaseModel):
    device_token: str
    title: str
    body: str