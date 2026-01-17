from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.exceptions import InternalServerError
from app.db.session import get_session
from app.db.models import User
from app.core.logging import logger
from app.schemas.explore import ExploreTabVideosResponse, ExploreTabEbooksResponse, ExploreTabInProgressResponse, ExploreTabDiysResponse
from app.services.auth import get_user_from_access_token
from app.utils.ebook import get_new_ebooks
from app.utils.video import get_new_videos
from app.utils.my_explorer import get_adventures_in_progress
from app.utils.adventure import get_series_adventures


router = APIRouter(prefix="/explore-tab", tags=["ExploreTab"])


@router.get("/videos")
async def explore_videos(
    q: Optional[str] = Query(None),
    offset: int = Query(0),
    limit: int = Query(10),
    min_similarity: float = Query(0.1, ge=0, le=1),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_user_from_access_token)
):
    try:

        videos = await get_new_videos(
            session=session,
            offset=offset,
            limit=limit,
            min_similarity=min_similarity,
            q=q
        )

        return ExploreTabVideosResponse(videos=videos)

    except Exception as e:
        logger.error("Error getting videos for explore tab: {}", str(e), exc_info=True)
        raise InternalServerError()
    
    


@router.get("/ebooks")
async def explore_ebooks(
    q: Optional[str] = Query(None),
    offset: int = Query(0),
    limit: int = Query(10),
    min_similarity: float = Query(0.1, ge=0, le=1),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_user_from_access_token)
):
    try:

        ebooks = await get_new_ebooks(
            session=session,
            offset=offset,
            limit=limit,
            min_similarity=min_similarity,
            q=q
        )

        return ExploreTabEbooksResponse(ebooks=ebooks)

    except Exception as e:
        logger.error("Error getting ebooks for explore tab: {}", str(e), exc_info=True)
        raise InternalServerError()
    
    
@router.get("/in-progress")
async def explore_in_progress(
    profile_id: Optional[UUID] = Query(None),
    q: Optional[str] = Query(None),
    offset: int = Query(0),
    limit: int = Query(10),
    min_similarity: float = Query(0.1, ge=0, le=1),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_user_from_access_token)
):
    try:

        in_progress = await get_adventures_in_progress(
            profile_id=profile_id,
            session=session,
            offset=offset,
            limit=limit,
            min_similarity=min_similarity,
            q=q
        ) if profile_id else []

        return ExploreTabInProgressResponse(adventures=in_progress)

    except Exception as e:
        logger.error("Error getting in-progress adventures for explore tab: {}", str(e), exc_info=True)
        raise InternalServerError()
    
    
@router.get("/diys")
async def explore_diys(
    q: Optional[str] = Query(None),
    offset: int = Query(0),
    limit: int = Query(10),
    min_similarity: float = Query(0.1, ge=0, le=1),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_user_from_access_token)
):
    try:

        diys = await get_series_adventures(
            series_name="DIY",
            session=session,
            offset=offset,
            limit=limit,
            min_similarity=min_similarity,
            q=q
        )

        return ExploreTabDiysResponse(adventures=diys)

    except Exception as e:
        logger.error("Error getting DIY adventures for explore tab: {}", str(e), exc_info=True)
        raise InternalServerError()