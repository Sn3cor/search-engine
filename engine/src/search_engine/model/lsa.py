
import joblib
import numpy as np

from search_engine.config import INDEX_PATH


class LsaModel:
    def __init__(self):
        self._vectorizer = None
        self._matrix = None
        self._doc_meta = None

    def load(self):
        self._matrix = np.load(INDEX_PATH / "lsa_matrix.npy")
        self._vectorizer = joblib.load(INDEX_PATH / "lsa_vectorizer.pkl")
        self._doc_meta = joblib.load(INDEX_PATH / "doc_meta.pkl")

    def search(self, query, top_n=10):
        query_vec = self._vectorizer.transform([query])
        norm = np.linalg.norm(query_vec)
        if norm == 0:
            return []

        scores = (query_vec @ self._matrix).flatten()
        top_n = min(top_n, scores.size)
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
            if scores[i] > 0
        ]
