from fastapi import FastAPI
from search_endpoint import router as search_router
from topic_endpoint import router as topic_router
from entity_endpoint import router as entity_router

app = FastAPI(title="News REST API")

app.include_router(search_router, prefix="/api/search", tags=["Search"])
app.include_router(topic_router, prefix="/api/topics", tags=["Topics"])
app.include_router(entity_router, prefix="/api/entities", tags=["Entities"])
