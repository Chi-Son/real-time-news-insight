from fastapi import APIRouter, Query

router = APIRouter()

@router.get("/")
def search(
    q: str = Query(..., description="topic or entity keyword"),
    limit: int = 20
):
    return {
        "query": q,
        "limit": limit,
        "message": "TODO: search by topic + entity"
    }
