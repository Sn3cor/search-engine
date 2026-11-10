from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from search_engine.indexer import index_exists, run_setup_pipeline
from search_engine.model.bm25 import Bm25Model
from search_engine.model.bow import BowModel
from search_engine.model.lsa import LsaModel


class SearchRequest(BaseModel):
    query: str
    top_n: int = 10

class SearchResult(BaseModel):
    rank: int
    page_id: int
    title: str
    url: str
    score: float

class SearchResponse(BaseModel):
    bow: list[SearchResult]
    lsa: list[SearchResult]
    bm25: list[SearchResult]

bow = BowModel()
lsa = LsaModel()
bm25 = Bm25Model()

@asynccontextmanager
async def lifespan(app: FastAPI):
    if not index_exists():
        print("Index not found - running setup")
        run_setup_pipeline()
    bow.load()
    lsa.load()
    bm25.load()
    yield

origins = [
    "http://localhost:5173",
    "http://localhost:8000",
]

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/search")
def search(request: SearchRequest, response_model=SearchResponse):
    return {
        "bow": bow.search(request.query, request.top_n),
        "lsa": lsa.search(request.query, request.top_n),
        "bm25": bm25.search(request.query, request.top_n),
    }
