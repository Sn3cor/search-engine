import joblib
import numpy as np
from pathlib import Path

INDEX_PATH = Path(__file__).parent.parent.parent / "data" / "index"


class LsaIndex:
    def __init__(self):
        self._svd = None
        self._vectorizer = None
        self._doc_meta = None
        self._vectors_norm = None

    def load(self):
        lsa_vectors = np.load(INDEX_PATH / "lsa_matrix.npy") 
        self._svd = joblib.load(INDEX_PATH / "svd_model.pkl")
        self._vectorizer = joblib.load(INDEX_PATH / "tfidf_vectorizer.pkl")
        self._doc_meta = joblib.load(INDEX_PATH / "doc_meta.pkl")

        col_norms = np.linalg.norm(lsa_vectors, axis=0, keepdims=True)
        col_norms[col_norms == 0] = 1
        self._vectors_norm = lsa_vectors / col_norms  

    def search(self, query, top_n = 10):
        query_tfidf = self._vectorizer.transform([query])
        query_lsa = self._svd.transform(query_tfidf)            

        norm = np.linalg.norm(query_lsa)
        if norm == 0:
            return []

        scores = ((query_lsa / norm) @ self._vectors_norm).flatten()  

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
