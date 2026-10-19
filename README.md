# search-engine


## Project structure

```
search-engine/
├── engine/                          # uv workspace root and the search-engine package
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── data/                        # Corpus and index, created by the crawler and indexer
│   ├── packages/
│   │   └── crawler/                 # Workspace member with its own dependencies
│   │       ├── pyproject.toml
│   │       └── src/crawler/
│   │           └── crawler.py       # BFS crawler over Wikipedia categories
│   ├── scripts/
│   │   └── compare_models.py        # Script for testing the models without the REST API
│   └── src/search_engine/
│       ├── preprocessor.py          # Corpus tokenization and stemming functions
│       ├── indexer.py               # Index building (BoW with TF-IDF, BM25, LSA)
│       ├── api/
│       │   └── main.py              # REST API (FastAPI)
│       └── model/
│           ├── bow.py               # Bag of Words model with TF-IDF
│           ├── bm25.py              # BM25 model
│           └── lsa.py               # LSA model (Latent Semantic Analysis)
└── frontend/                        # Client application
```

---

## Dataset
The search engine is built on 100,000 Wikipedia articles from the History category. In every model the vocabulary is limited to 70,000 words.


## "Crawler"

Strictly speaking this is not a real crawler that walks web pages and downloads their full HTML, because it uses the API provided by Wikipedia. The whole script is based on the BFS algorithm. When it reaches a category page, the linked article pages are fetched through the API and the subcategory pages are queued. The crawler lets you configure the starting category as a `Category:<Category>` string, the number of articles to save, and the maximum category depth the algorithm will descend to. I used BFS so that the fetched articles are related to the starting category. I also added protection against getting stuck in a cycle by remembering visited categories. No article is fetched twice either, because the page_id of every fetched article is remembered.
Each article is saved as one line in `engine/data/data.jsonl` in the form:

```json
{
    "id": 00000,
    "title": "Title",
    "url": "https://en.wikipedia.org/wiki/Article",
    "text": "Article text"
}
```

## Text preprocessing
Every vectorizer used in the indexing process uses the `preprocess` function from `engine/src/search_engine/preprocessor.py`. Its job is to normalize the input text, which includes converting it to lowercase and removing unnecessary characters. Common words that carry no semantic meaning (stop words) are also filtered out. The remaining tokens are then reduced to their stems with the Porter Stemmer algorithm.

## Indexing

After the data is collected, each model builds the objects it needs and saves them to files in the `engine/data/index` directory.

| File | Model | Contents |
|---|---|---|
| `tfidf_matrix.npz` | BoW | Sparse TF-IDF matrix |
| `tfidf_vectorizer.pkl` | BoW, LSA | Fitted `TfidfVectorizer` (query transformation) |
| `lsa_matrix.npy` | LSA | Dense LSA matrix |
| `svd_model.pkl` | LSA | Fitted `TruncatedSVD` (query projection for LSA) |
| `bm25_matrix.npz` | BM25 | BM25+ weight matrix |
| `bm25_vectorizer.pkl` | BM25 | Fitted `BM25Vectorizer` |
| `doc_meta.pkl` | all | Document metadata: `page_id`, `title`, `url` |

## Search models

### Bag of Words with TF-IDF
Documents are processed with a TfidfVectorizer into column vectors with TF-IDF (Term Frequency - Inverse Document Frequency) weights. For each word in a given document the following is computed:
```math
tfidf(t,d,D) = tf(t,d) \cdot idf(t,D)
```
where:

$t$ - a word (after stemming),

$d$ - a document (after stemming),

$D$ - the set of all documents (after stemming),

$tf(t, d) = 1 + \ln(f_{t,d})$ - the frequency of word $t$ in document $d$; $f_{t,d}$ - the number of occurrences of word $t$ in document $d$,

$idf(t,D) = \ln\left(\frac{N + 1}{n_t + 1}\right) + 1$ - the inverse frequency of word $t$ across $N = |D|$ documents; $n_t$ - the number of documents containing word $t$

The query vector is transformed in the same way. Similarity is computed as the cosine between the query vector and every document vector in the matrix.

The result is the $top_n=10$ documents with the highest similarity.

### LSA (Latent Semantic Analysis)
A matrix is built the same way as in the Bag of Words with TF-IDF model, but it is decomposed into three matrices using SVD and then approximated to rank 200 with TruncatedSVD from the sklearn package. When the model is loaded to serve queries, every corpus vector is normalized.

The query is first transformed by the TfidfVectorizer, then reduced to the same dimension by the previously saved TruncatedSVD model, and normalized. As in the BoW model, similarity is computed as the cosine of the angle between the query vector and every document vector in the matrix.

The result is the $top_n=10$ documents with the highest similarity.

### BM25
To compute the BM25 weights I used the [`bm25-vectorizer`](https://pypi.org/project/bm25-vectorizer/) package with the `bm25plus` variant. Documents are transformed with a BM25Vectorizer into a matrix of weights computed for every word in every document according to the formula:
$$S(t, d) = idf(t) \cdot \left( \frac{f_{t,d} \cdot (k_1 + 1)}{f_{t,d} + k_1 \cdot \left(1 - b + b \cdot \frac{|d|}{avgdl}\right)} + \delta \right)$$
where:

$idf(t,D) = \ln\left(\frac{N + 1}{n_t}\right)$ - the inverse frequency of word $t$ across $N = |D|$ documents; $n_t$ - the number of documents containing word $t$;

$f_{t,d}$ - the number of occurrences of word $t$ in document $d$,

$|d|$ - the length of document $d$

$avgdl$ - the average document length in the collection

$k_1$ - the term frequency saturation parameter

$b$ - the document length penalty parameter

$\delta$ - the minimum reward for the presence of a word

The query is transformed into a vector $q$ that counts the occurrences of each keyword. The score vector $s$ is then computed as the product of the query vector and the weight matrix $W$
```math
s = qW
```
The score for a given document $s_d$ is the product of the vector $q$ and the document's column vector $w_d$:

```math
s_d = qw_d = \sum_{i=1}^{V} q_i W_{i,d}
```
The result is the $top_n=10$ documents with the highest scores.

---

## Installing the required packages

The backend is a [uv](https://docs.astral.sh/uv/) workspace. A single command installs both the search engine and the crawler into one shared environment:

```bash
cd engine
uv sync --all-packages
```

---

## Running

All commands are run from the `engine/` directory.

### 1. Collecting data (crawler)

```bash
uv run --package crawler crawl
```

`--package crawler` is needed because `uv run` targets the workspace root (the search engine) by default. The crawler starts from the `Category:History` category with a depth of 5.

### 2. Building the index

The index is built automatically the first time the API starts. You can also build it manually beforehand:

```bash
uv run se-index
```

### 3. Starting the API

```bash
uv run fastapi dev src/search_engine/api/main.py
```

The server will be available at `http://127.0.0.1:8000`.

## Example queries

Simple query: `the plague`

```bash
curl -X POST http://127.0.0.1:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "the plague", "top_n": 1}'
```

Example response with $top_n = 1$

```json
{
  "bow": [
    {
      "rank": 1,
      "page_id": 80232070,
      "title": "The Tenth Plague of Egypt",
      "url": "https://en.wikipedia.org/wiki/The_Tenth_Plague_of_Egypt",
      "score": 0.2138948825142888
    }
  ],
  "lsa": [
    {
      "rank": 1,
      "page_id": 63346478,
      "title": "412BC epidemic",
      "url": "https://en.wikipedia.org/wiki/412_BC_epidemic",
      "score": 0.4553370204456878
    }
  ],
  "bm25": [
    {
      "rank": 1,
      "page_id": 55586589,
      "title": "21st-century Madagascar plague outbreaks",
      "url": "https://en.wikipedia.org/wiki/21st-century_Madagascar_plague_outbreaks",
      "score": 13.42071398310949
    }
  ]
}
```

---

More descriptive query: `terrible disease outbreak that killed a massive part of the population in europe`

```bash
curl -X POST http://127.0.0.1:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "terrible disease outbreak that killed a massive part of the population in europe", "top_n": 1}'
```

Example response with $top_n = 1$


```json
{
  "bow": [
    {
      "rank": 1,
      "page_id": 49115045,
      "title": "List of anthrax outbreaks",
      "url": "https://en.wikipedia.org/wiki/List_of_anthrax_outbreaks",
      "score": 0.21537201635420986
    }
  ],
  "lsa": [
    {
      "rank": 1,
      "page_id": 945818,
      "title": "Listof epidemics and pandemics",
      "url": "https://en.wikipedia.org/wiki/List_of_epidemics_and_pandemics",
      "score": 0.5399005996166855
    }
  ],
  "bm25": [
    {
      "rank": 1,
      "page_id": 4501,
      "title": "Black Death",
      "url": "https://en.wikipedia.org/wiki/Black_Death",
      "score": 45.91318576446975
    }
  ]
}
```

## Running the client application

```sh
cd frontend
npm install
npm run dev
```
