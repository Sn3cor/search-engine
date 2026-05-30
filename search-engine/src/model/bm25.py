import joblib
import numpy as np
import scipy.sparse as sp
from pathlib import Path

from src.preprocessor import preprocess

INDEX_PATH = Path(__file__).parent.parent.parent / "data" / "index"


class Bm25Index:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.K1 = k1
        self.B = b
        self._matrix = None
        self._vocabulary = None
        self._doc_meta = None
        self._N = None
        self._doc_lengths = None
        self._avg_dl = None
        self._idf = None

    def load(self):
        self._matrix = sp.load_npz(INDEX_PATH / "bow_matrix.npz")  
        stats = joblib.load(INDEX_PATH / "bm25_stats.pkl")
        self._vocabulary = joblib.load(INDEX_PATH / "vocabulary.pkl")
        self._doc_meta = joblib.load(INDEX_PATH / "doc_meta.pkl")

        self._N = stats["N"]
        self._doc_lengths = stats["doc_lengths"]
        self._avg_dl = stats["avg_dl"]
        df = np.diff(self._matrix.indptr)
        self._idf = np.log((self._N - df + 0.5) / (df + 0.5) + 1)

    def search(self, query, top_n = 10):
        stems = preprocess(query)
        row_indices = [self._vocabulary[s] for s in stems if s in self._vocabulary]

        if not row_indices:
            return []

        scores = np.zeros(self._N)
        for row in row_indices:
            tf = self._matrix.getrow(row).toarray().flatten().astype(float)
            scores += self._idf[row] * (tf * (self.K1 + 1)) / (
                tf +self.K1 * (1 - self.B + self.B * self._doc_lengths / self._avg_dl)
            )

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
