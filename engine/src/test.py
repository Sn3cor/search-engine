from src.model.bow import BowIndex
from src.model.bm25 import Bm25Index
from src.model.lsa import LsaIndex

bow = BowIndex()
bm25 = Bm25Index()
lsa = LsaIndex()

bow.load()
lsa.load()
bm25.load()

QUERY = "Polish wars"


def print_results(model_name: str, results: list[dict]) -> None:
    print(f"\n{'='*60}")
    print(f"  {model_name}  |  query: \"{QUERY}\"")
    print(f"{'='*60}")
    print(f"  {'#':<4} {'Score':<8} {'Title'}")
    print(f"  {'-'*4} {'-'*8} {'-'*40}")
    for r in results:
        print(f"  {r['rank']:<4} {r['score']:<8.4f} {r['title']}")
    print()


print_results("BoW / TF-IDF", bow.search(QUERY))
print_results("LSA         ", lsa.search(QUERY))
print_results("BM25        ", bm25.search(QUERY))
