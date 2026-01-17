import logging
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn

from app.core.exceptions import ErrorCode, ResourceNotFoundError
from app.db.session import init_db

from app.api.v1.routers.auth import router as AuthRouter
from app.api.v1.routers.users import router as UserRouter
from app.api.v1.routers.classrooms import router as ClassroomRouter
from app.api.v1.routers.profiles import router as ProfileRouter
from app.api.v1.routers.avatars import router as AvatarRouter
from app.api.v1.routers.videos import router as VideoRouter
from app.api.v1.routers.themes import router as ThemeRouter
from app.api.v1.routers.ebooks import router as EbookRouter
from app.api.v1.routers.adventures import router as AdventureRouter
from app.api.v1.routers.gcs_urls import router as GCSUrlsRouter
from app.api.v1.routers.quizzes import router as QuizRouter
from app.api.v1.routers.questions import router as QuestionRouter
from app.api.v1.routers.quiz_attempts import router as QuizAttemptRouter
from app.api.v1.routers.quiz_responses import router as QuizResponseRouter
from app.api.v1.routers.adventure_progress import router as AdventureProgressRouter
from app.api.v1.routers.my_explorer_tab import router as MyExplorerTabRouter
from app.api.v1.routers.notifications import router as NotificationsRouter
from app.api.v1.routers.redirects import router as RedirectsRouter
from app.api.v1.routers.series import router as SeriesRouter
from app.api.v1.routers.explore_tab import router as ExploreTabRouter
from app.api.v1.routers.stats import router as StatsRouter
from app.api.v1.routers.ebooks_tab import router as EbooksTabRouter
from app.api.v1.routers.videos_tab import router as VideoTabRouter
from app.core.rate_limiter import init_rate_limiter
from slowapi.errors import RateLimitExceeded


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
        

app=FastAPI(
    # lifespan=lifespan,
    title="Wonderspaced API",
    version="1.0",
    debug=True,
)

init_rate_limiter(app)

api_v1_prefix = "/api/v1"

app.include_router(AuthRouter, prefix=api_v1_prefix)
app.include_router(UserRouter, prefix=api_v1_prefix)
app.include_router(ClassroomRouter, prefix=api_v1_prefix)
app.include_router(ProfileRouter, prefix=api_v1_prefix)
app.include_router(AvatarRouter, prefix=api_v1_prefix)
app.include_router(VideoRouter, prefix=api_v1_prefix)
app.include_router(ThemeRouter, prefix=api_v1_prefix)
app.include_router(EbookRouter, prefix=api_v1_prefix)
app.include_router(AdventureRouter, prefix=api_v1_prefix)
app.include_router(GCSUrlsRouter, prefix=api_v1_prefix)
app.include_router(QuizRouter, prefix=api_v1_prefix)
app.include_router(QuestionRouter, prefix=api_v1_prefix)
app.include_router(QuizAttemptRouter, prefix=api_v1_prefix)
app.include_router(QuizResponseRouter, prefix=api_v1_prefix)
app.include_router(AdventureProgressRouter, prefix=api_v1_prefix)
app.include_router(MyExplorerTabRouter, prefix=api_v1_prefix)
app.include_router(NotificationsRouter, prefix=api_v1_prefix)
app.include_router(RedirectsRouter, prefix=api_v1_prefix)
app.include_router(SeriesRouter, prefix=api_v1_prefix)
app.include_router(ExploreTabRouter, prefix=api_v1_prefix)
app.include_router(StatsRouter, prefix=api_v1_prefix)
app.include_router(EbooksTabRouter, prefix=api_v1_prefix)
app.include_router(VideoTabRouter, prefix=api_v1_prefix)
    
    
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    error_code = exc.detail.get("error_code", ErrorCode.HTTP_ERROR.value) if isinstance(exc.detail, dict) else ErrorCode.HTTP_ERROR.value  
    message = exc.detail.get("message") if isinstance(exc.detail, dict) else exc.detail

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": False,
            "error_code": error_code,
            "message": message,
            "data": None
        }
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": False,
            "error_code": ErrorCode.INTERNAL_SERVER_ERROR.value,
            "message": "Something went wrong at our end. Please try again later",
        }
    )
    
    
    
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        field = error["loc"][-1]
        message = error["msg"]
        errors.append({
            'field': field,
            'message': message
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": False,
            "error_code": ErrorCode.VALIDATION_ERROR.value,
            "message": "Validation failed",
            "data": {"errors": errors}
        }
    )
    
    
@app.exception_handler(ResourceNotFoundError)
async def method_not_allowed_exception_handler(request: Request, exc: ResourceNotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "status": False,
            "error_code": exc.detail.get("error_code", ErrorCode.HTTP_ERROR.value),
            "message": exc.detail.get("message"),
            "data": None
        }
    )


@app.get("/")
async def root():
    return {"message": "Hello Explorer!"}


origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
port = int(os.environ.get("PORT", 8080)) 

if __name__ == '__main__':
   uvicorn.run("main:app", port=port, host="0.0.0.0", reload=True)