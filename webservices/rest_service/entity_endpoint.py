from fastapi import APIRouter

router = APIRouter()

@router.get("/{entity_id}/articles")
def get_entity_articles(entity_id: str):
    return {"entity_id": entity_id, "message": "TODO: articles"}

@router.get("/{entity_id}/articles/history")
def get_entity_articles_history(entity_id: str):
    return {"entity_id": entity_id, "message": "TODO: history"}
