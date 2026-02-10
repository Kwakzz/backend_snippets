import json
import firebase_admin
from firebase_admin import credentials

from app.core.config import settings


cred = credentials.Certificate(
    json.loads(settings.FIREBASE_SERVICE_ACCOUNT_KEY)
)
firebase_admin.initialize_app(cred)