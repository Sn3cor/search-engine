import json
import joblib
import nltk
import numpy as np
import scipy.sparse as sp
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from bm25_vectorizer import BM25Vectorizer

from src.preprocessor import preprocess

DATA_PATH = Path(__file__).parent.parent / "data" / "data1.jsonl"
INDEX_PATH = Path(__file__).parent.parent / "data" / "index"
VOCAB_SIZE = 70_000
LSA_COMPONENTS = 200
BM25_K1 = 1.5
BM25_B = 0.75

def index_exists():
    required = [
        "tfidf_matrix.npz",
        "lsa_matrix.npy",
        "tfidf_vectorizer.pkl",
        "svd_model.pkl",
        "bm25_matrix.npz",
        "bm25_vectorizer.pkl",
        "doc_meta.pkl",
    ]

    return all((INDEX_PATH / f).exists() for f in required)

def load_documents():
    texts: list[str] = []
    doc_meta: list[dict] = []

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            doc = json.loads(line)
            text = doc.get("text", "").strip()
            title = doc.get("title", "").strip()
            if not text:
                continue
            texts.append(title + " " + text)
            doc_meta.append({"page_id": doc["id"], "title": title, "url": doc.get("url", "")})


    print(f"  loaded {len(texts)} documents")
    return texts, doc_meta


def build_tfidf(texts):
    vectorizer = TfidfVectorizer(
        analyzer=preprocess,
        max_features=VOCAB_SIZE,
        min_df=2,          
        sublinear_tf=True, 
    )
    tfidf_matrix = vectorizer.fit_transform(texts)
    print(f"  TF-IDF matrix: {tfidf_matrix.shape}, {tfidf_matrix.nnz} non-zeros")
    return tfidf_matrix, vectorizer


def build_bm25(texts):
    vectorizer = BM25Vectorizer(
        analyzer=preprocess,
        transformer="bm25plus",
        max_features=VOCAB_SIZE,
        min_df=2,
        k1=BM25_K1,
        b=BM25_B,
    )
    bm25_matrix = vectorizer.fit_transform(texts)
    print(f"  BM25 matrix: {bm25_matrix.shape}, {bm25_matrix.nnz} non-zeros")
    return vectorizer, bm25_matrix


def build_lsa(tfidf_matrix) :
    svd = TruncatedSVD(n_components=LSA_COMPONENTS, random_state=42)
    lsa_vectors = svd.fit_transform(tfidf_matrix)  
    variance = svd.explained_variance_ratio_.sum()
    print(f"  LSA variance explained: {variance * 100:.2f}%")
    print(f"  LSA: {lsa_vectors.shape}")
    return lsa_vectors, svd


def run_setup_pipeline():
    nltk.download('stopwords')
    nltk.download('punkt_tab')
    INDEX_PATH.mkdir(parents=True, exist_ok=True)

    print("\nLoading documents")
    texts, doc_meta = load_documents()

    print("\nBuilding TF-IDF matrix")
    tfidf_matrix, tfidf_vec = build_tfidf(texts)

    print("\nBuilding BM25 matrix")
    bm25_vec, bm25_matrix = build_bm25(texts)

    print("\nBuilding LSA matrix")
    lsa_matrix, svd = build_lsa(tfidf_matrix)


    joblib.dump(doc_meta, INDEX_PATH / "doc_meta.pkl")

    joblib.dump(tfidf_vec, INDEX_PATH / "tfidf_vectorizer.pkl")

    sp.save_npz(INDEX_PATH / "tfidf_matrix.npz", tfidf_matrix.T.tocsr())

    joblib.dump(bm25_vec, INDEX_PATH / "bm25_vectorizer.pkl")
    sp.save_npz(INDEX_PATH / "bm25_matrix.npz", bm25_matrix.T.tocsr())

    np.save(INDEX_PATH / "lsa_matrix.npy", lsa_matrix.T)
    joblib.dump(svd, INDEX_PATH / "svd_model.pkl")

    print(f"\nDone. Index written to {INDEX_PATH}")


if __name__ == "__main__":
    print(index_exists())
    run_setup_pipeline()
