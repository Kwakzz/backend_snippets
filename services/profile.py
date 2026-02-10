from app.db.models import UserProfile
from sqlmodel import func


def search_profile(
    existing_query, 
    q: str
):
    query = existing_query.where(
        func.to_tsvector('english', UserProfile.first_name + ' ' + UserProfile.last_name).bool_op('@@')(
            func.plainto_tsquery('english', q)
        )
    ).order_by(
        func.ts_rank_cd(
            func.to_tsvector('english', UserProfile.first_name + ' ' + UserProfile.last_name),
            func.plainto_tsquery('english', q)
        ).desc()
    )
    
    return query