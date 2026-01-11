from fastapi import FastAPI
from search_endpoint import router as search_router
from topic_endpoint import router as topic_router
from entity_endpoint import router as entity_router
from source_endpoint import router as source_router
from category_endpoint import router as category_router
from lastest_article import router as article_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="News REST API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search_router, tags=["Search"])
app.include_router(topic_router, tags=["Topics"])
app.include_router(entity_router, tags=["Entities"])
app.include_router(source_router, tags=["Source"])
app.include_router(category_router, tags=["Category"])
app.include_router(article_router, tags=["Article"])
