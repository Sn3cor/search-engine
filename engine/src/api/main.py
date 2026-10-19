from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager

from src.model.bow import BowIndex
from src.model.bm25 import Bm25Index
from src.model.lsa import LsaIndex
from src.indexer import index_exists, run_setup_pipeline

bow = BowIndex()
lsa = LsaIndex()
bm25 = Bm25Index()


class SearchRequest(BaseModel):
    query: str
    top_n: int = 10


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not index_exists():
        run_setup_pipeline()
    bow.load()
    lsa.load()
    bm25.load()
    yield


app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:5173",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/search")
def search(request: SearchRequest):
    return {
        "bow":  bow.search(request.query, request.top_n),
        "lsa":  lsa.search(request.query, request.top_n),
        "bm25": bm25.search(request.query, request.top_n),
    }
