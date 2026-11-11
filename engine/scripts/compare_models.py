from search_engine.model.bm25 import Bm25Model
from search_engine.model.bow import BowModel
from search_engine.model.lsa import LsaModel

QUERIES = ["Polish wars", "World War II", "Plague", "Uprising"]


def print_results(query: str, by_model: dict[str, list[dict]]) -> None:
    print(f"\n{'=' * 60}")
    print(f'query: "{query}"')
    for name, hits in by_model.items():
        print("=" * 60)
        print(f"  model: {name}")
        if not hits:
            print("  (no results)")
            continue
        print(f"  {'#':<4} {'Score':<8} Title")
        print(f"  {'-' * 4} {'-' * 8} {'-' * 40}")
        for hit in hits:
            print(f"  {hit['rank']:<4} {hit['score']:<8.4f} {hit['title']}")
    print()


def main() -> None:
    models = {"BoW/TF-IDF": BowModel(), "BM25+": Bm25Model(), "LSA": LsaModel()}
    for model in models.values():
        model.load()

    for query in QUERIES:
        print_results(query, {name: m.search(query) for name, m in models.items()})


if __name__ == "__main__":
    main()
