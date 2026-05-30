import joblib
import numpy as np
import scipy.sparse as sp
from pathlib import Path

INDEX_PATH = Path(__file__).parent.parent.parent / "data" / "index"


class BowIndex:
    def __init__(self):
        self._vectorizer = None
        self._matrix = None
        self._doc_meta = None

    def load(self):
        self._vectorizer = joblib.load(INDEX_PATH / "tfidf_vectorizer.pkl")
        self._matrix = sp.load_npz(INDEX_PATH / "tfidf_matrix.npz")  
        self._doc_meta = joblib.load(INDEX_PATH / "doc_meta.pkl")

    def search(self, query, top_n = 10):
        query_vec = self._vectorizer.transform([query])          
        query_norm = np.sqrt(query_vec.multiply(query_vec).sum())
        if query_norm == 0:
            return []

        scores = (query_vec @ self._matrix).toarray().flatten() / query_norm

        top_indices = np.argpartition(scores, -top_n)[-top_n:]
        top_indices = top_indices[np.argsort(scores[top_indices])[::-1]]

        return [
            {
                "rank": rank + 1,
                "page_id": self._doc_meta[i]["page_id"],
                "title": self._doc_meta[i]["title"],
                "url": self._doc_meta[i]["url"],
                "score": float(scores[i]),
            }
            for rank, i in enumerate(top_indices)
        ]
