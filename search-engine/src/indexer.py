import json
import joblib
import nltk
import numpy as np
import scipy.sparse as sp
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import TruncatedSVD

from src.preprocessor import preprocess

DATA_PATH = Path(__file__).parent.parent / "data" / "data1.jsonl"
INDEX_PATH = Path(__file__).parent.parent / "data" / "index"
VOCAB_SIZE = 70_000
LSA_COMPONENTS = 300

def index_exists():
    required = [
        "tfidf_matrix.npz",
        "bow_matrix.npz",
        "lsa_vectors.npy",
        "tfidf_vectorizer.pkl",
        "svd_model.pkl",
        "doc_meta.pkl",
        "vocabulary.pkl",
        "bm25_stats.pkl",
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


def build_tfidf_matrix(texts):
    vectorizer = TfidfVectorizer(
        analyzer=preprocess,
        max_features=VOCAB_SIZE,
        min_df=2,          
        sublinear_tf=True, 
    )
    tfidf_matrix = vectorizer.fit_transform(texts)
    print(f"  TF-IDF matrix: {tfidf_matrix.shape}, {tfidf_matrix.nnz} non-zeros")
    return tfidf_matrix, vectorizer


def build_bm25_stats(texts, vocabulary):
    count_vectorizer = CountVectorizer(
        analyzer=preprocess,
        vocabulary=vocabulary,
    )
    bow_matrix = count_vectorizer.fit_transform(texts)  # (n_docs, vocab) raw counts

    doc_lengths = np.array(bow_matrix.sum(axis=1)).flatten()  # sum across terms per doc
    avg_dl = float(doc_lengths.mean())
    N = bow_matrix.shape[0]

    print(f"  BM25: {N} docs, avg length {avg_dl:.1f} tokens")
    return {
        "bow_matrix": bow_matrix,
        "doc_lengths": doc_lengths,
        "avg_dl": avg_dl,
        "N": N,
    }


def build_lsa_vectors(tfidf_matrix) :
    svd = TruncatedSVD(n_components=LSA_COMPONENTS, random_state=42)
    lsa_vectors = svd.fit_transform(tfidf_matrix)  # (n_docs, LSA_COMPONENTS)
    print(f"  LSA: {lsa_vectors.shape}")
    return lsa_vectors, svd


def run_setup_pipeline():
    nltk.download('stopwords')
    nltk.download('punkt_tab')
    INDEX_PATH.mkdir(parents=True, exist_ok=True)

    print("\n[1/4] Loading documents")
    texts, doc_meta = load_documents()

    print("\n[2/4] Building TF-IDF matrix")
    tfidf_matrix, tfidf_vec = build_tfidf_matrix(texts)
    vocabulary = tfidf_vec.vocabulary_  # {stem: col_index}, shared by all models

    print("\n[3/4] Building BM25 stats")
    bm25 = build_bm25_stats(texts, vocabulary)

    print("\n[4/4] Building LSA vectors")
    lsa_vectors, svd = build_lsa_vectors(tfidf_matrix)

    print("\nSaving files...")

    joblib.dump(doc_meta, INDEX_PATH / "doc_meta.pkl")

    joblib.dump(vocabulary, INDEX_PATH / "vocabulary.pkl")

    joblib.dump(tfidf_vec, INDEX_PATH / "tfidf_vectorizer.pkl")

    sp.save_npz(INDEX_PATH / "tfidf_matrix.npz", tfidf_matrix.T.tocsr())

    sp.save_npz(INDEX_PATH / "bow_matrix.npz", bm25["bow_matrix"].T.tocsr())

    bm25_stats = {k: v for k, v in bm25.items() if k != "bow_matrix"}
    joblib.dump(bm25_stats, INDEX_PATH / "bm25_stats.pkl")

    np.save(INDEX_PATH / "lsa_vectors.npy", lsa_vectors.T)
    joblib.dump(svd, INDEX_PATH / "svd_model.pkl")

    print(f"\nDone. Index written to {INDEX_PATH}")


if __name__ == "__main__":
    print(index_exists())
    run_setup_pipeline()
