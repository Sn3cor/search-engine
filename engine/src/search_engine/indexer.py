import joblib
import numpy as np
import pandas as pd
import scipy.sparse as sp
from bm25_vectorizer import BM25Vectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import Normalizer

from search_engine.config import DATA_PATH, INDEX_PATH
from search_engine.preprocessor import preprocess

VOCAB_SIZE = 70_000
LSA_COMPONENTS = 200
BM25_K1 = 1.5
BM25_B = 0.75


def index_exists():
    required = [
        "tfidf_matrix.npz",
        "tfidf_vectorizer.pkl",
        "bm25_matrix.npz",
        "bm25_vectorizer.pkl",
        "lsa_matrix.npy",
        "lsa_vectorizer.pkl",
        "doc_meta.pkl",
    ]

    return all((INDEX_PATH / f).exists() for f in required)


def load_documents() -> tuple[pd.Series, pd.DataFrame]:
    df = (
        pd.read_json(DATA_PATH, lines=True, dtype=False)
        .reindex(columns=["id", "title", "text", "url"])
        .fillna({"title": "", "text": "", "url": ""})
        .assign(
            title=lambda d: d["title"].str.strip(),
            text=lambda d: d["text"].str.strip(),
        )
        .loc[lambda d: d["text"] != ""]
        .rename(columns={"id": "page_id"})
        .reset_index(drop=True)
    )
    print(f"  loaded {len(df)} documents")
    return df["title"] + " " + df["text"], df[["page_id", "title", "url"]]


def build_tfidf(corpus) -> tuple[sp.csr_matrix, TfidfVectorizer]:
    vectorizer = TfidfVectorizer(
        analyzer=preprocess,
        max_features=VOCAB_SIZE,
        min_df=2,
        sublinear_tf=True,
    )
    tfidf_matrix = vectorizer.fit_transform(corpus)
    print(f"  TF-IDF matrix: {tfidf_matrix.shape}, {tfidf_matrix.nnz} non-zeros")
    return tfidf_matrix, vectorizer


def build_bm25(corpus) -> tuple[sp.csr_matrix, CountVectorizer]:
    bm25 = BM25Vectorizer(
        analyzer=preprocess,
        transformer="bm25plus",
        max_features=VOCAB_SIZE,
        min_df=2,
        k1=BM25_K1,
        b=BM25_B
    )
    bm25_matrix = bm25.fit_transform(corpus)
    query_vectorizer = CountVectorizer(analyzer=preprocess, vocabulary=bm25.vocabulary_)
    print(f"  BM25 matrix: {bm25_matrix.shape}, {bm25_matrix.nnz} non-zeros")
    return bm25_matrix, query_vectorizer


def build_lsa(tfidf_matrix, tfidf_vectorizer) -> tuple[np.ndarray, Pipeline]:
    svd = TruncatedSVD(n_components=LSA_COMPONENTS, random_state=42)
    svd_norm = make_pipeline(svd, Normalizer())
    lsa_vectors = svd_norm.fit_transform(tfidf_matrix)
    variance = svd.explained_variance_ratio_.sum()
    print(f"  LSA variance explained: {variance * 100:.2f}%")
    print(f"  LSA: {lsa_vectors.shape}")
    return lsa_vectors, make_pipeline(tfidf_vectorizer, svd_norm)


def run_setup_pipeline():
    INDEX_PATH.mkdir(parents=True, exist_ok=True)

    print("\nLoading documents")
    corpus, meta = load_documents()
    joblib.dump(meta.to_dict("records"), INDEX_PATH / "doc_meta.pkl")

    print("\nBuilding TF-IDF matrix")
    tfidf_matrix, tfidf_vec = build_tfidf(corpus)
    joblib.dump(tfidf_vec, INDEX_PATH / "tfidf_vectorizer.pkl")
    sp.save_npz(INDEX_PATH / "tfidf_matrix.npz", tfidf_matrix.T.tocsr())

    print("\nBuilding BM25 matrix")
    bm25_matrix, bm25_vec = build_bm25(corpus)
    joblib.dump(bm25_vec, INDEX_PATH / "bm25_vectorizer.pkl")
    sp.save_npz(INDEX_PATH / "bm25_matrix.npz", bm25_matrix.T.tocsr())

    print("\nBuilding LSA matrix")
    lsa_matrix, lsa_vec = build_lsa(tfidf_matrix, tfidf_vec)
    joblib.dump(lsa_vec, INDEX_PATH / "lsa_vectorizer.pkl")
    np.save(INDEX_PATH / "lsa_matrix.npy", lsa_matrix.T)


    print(f"\nDone. Index written to {INDEX_PATH}")


def main():
    print(index_exists())
    run_setup_pipeline()


if __name__ == "__main__":
    main()
