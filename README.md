# search-engine



---

## Struktura projektu

```
simple-browser/
├── search-engine/
│   ├── crawler/
│   │   └── main.py          # Crawler BFS po kategoriach Wikipedii
│   ├── src/
│   │   ├── preprocessor.py  # Tokenizacja, stemming (PorterStemmer) korpusu
│   │   ├── indexer.py       # Budowanie indeksu (TF-IDF, BM25, LSA)
│   │   ├── test.py          # Skrypt do testowania modeli bez REST API
│   │   ├── api/
│   │   │   └── main.py      # REST API (FastAPI)
│   │   └── model/
│   │       ├── bow.py       # Model Bag of Words / TF-IDF
│   │       ├── bm25.py      # Model BM25
│   │       └── lsa.py       # Model LSA (Latent Semantic Analysis)
│   └── requirements.txt
└── frontend/                # Aplikacja kliencka
```

---

## Crawler

W zasadzie nie jest to prawdziwy crawler, chodzący po stronach i zapisujący caly HTML, poniewaz wykorzystałem api udostępnione przez Wikipedię. 
Cały skrypt oparty jest o algorytm BFS i odwiedzanie kolejnych stron z artykułami lub kategoriami. W przypadku natrafienia na stronę kategorii, zbierane są podlinkownae tam strony z artykułami oraz kolejne strony z kategoriami. 
Crawler umozliwia skonfigurowanie kategorii początkowej w postaci stringa `Category:<Kategoria>`, ilości artykułów do zapisania oraz głębokości, do której masymalnie zejdzie algorytm. BFS został uzyty, poniewaz istnieje ryzyko wystąpienia cyklu, np. na głębokości 4 wystąpi strona kategorii z odnośnikiem do kategorii początkowej.
Kazdy artykuł zostaje zapisany jako linijka w `data/data.jsonl` w postaci:

```json
{
    "id": 00000
    "title": "Tytuł"
    "utl": "https://en.wikipedia.org/wiki/Artykuł"
    "text": "Tekst artykułu"
}
```

## Dataset
Wykorzystałem zbiorem danych jest 100 000 artykułów z angielskiej Wikipedii z kategorii Historia. Słownik 

## Indeksowanie


## Modele wyszukiwania

### Bag of Words / TF-IDF
Dokumenty i zapytania reprezentowane jako wektory TF-IDF w przestrzeni 70 000 słów. Podobieństwo obliczane jako cosinus kąta między wektorem zapytania a każdym dokumentem. Macierz dokumentów przechowywana w formacie rzadkim (scipy CSR).

### LSA (Latent Semantic Analysis)
Macierz TF-IDF redukowana do 300 wymiarów latentnych przy użyciu Truncated SVD (sklearn). Zapytanie rzutowane do tej samej przestrzeni przez dopasowany model SVD, następnie obliczane podobieństwo cosinusowe. LSA grupuje semantycznie powiązane terminy, nawet jeśli nie pojawiają się razem dosłownie.

### BM25
Klasyczny probabilistyczny model wyszukiwania. Wykorzystuje pakiet [`bm25-vectorizer`](https://pypi.org/project/bm25-vectorizer/) (zgodny ze scikit-learn). Dopasowany `BM25Vectorizer` przechowuje macierz surowych liczb wystąpień, IDF, długości dokumentów oraz średnią długość. Ranking liczony jest metodą `rank()`, która dla każdego termu z zapytania sumuje wynik BM25 uwzględniający częstość termu, częstość dokumentową oraz normalizację długości dokumentu (parametry `k1=1.5`, `b=0.75`).


---



## Wymagania

```bash
cd search-engine
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Uruchomienie

### 1. Zbieranie danych (crawler)

Crawler przechodzi po kategoriach Wikipedii metodą BFS i zapisuje artykuły do `data/data1.jsonl`.

```bash
cd search-engine
python crawler/main.py
```

Domyślnie pobiera do 100 000 artykułów z kategorii `Category:History` z głębokością 5.

### 2. Budowanie indeksu

Indeks budowany jest automatycznie przy pierwszym uruchomieniu API. Można też zbudować ręcznie:

```bash
cd search-engine
python -m src.indexer
```

Proces budowania indeksu:
1. Wczytanie dokumentów z `data/data1.jsonl` (pomijane artykuły bez treści)
2. Budowa macierzy TF-IDF (`min_df=2`, `sublinear_tf=True`)
3. Dopasowanie `BM25Vectorizer` (`k1=1.5`, `b=0.75`)
4. Redukcja SVD do 300 wymiarów (LSA)
5. Zapis artefaktów do `data/index/`

### 3. Uruchomienie API

```bash
cd search-engine
fastapi dev src/api/main.py
```

Serwer będzie dostępny pod `http://127.0.0.1:8000`, natomiast prosta dokumentacja pod `http://127.0.0.1:8000/docs`.

### 4. Zapytanie do API

```bash
curl -X POST http://127.0.0.1:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Roman Empire collapse", "top_n": 10}'
```

Przykładowa odpowiedź z `top_n = 1`

```json
Response body

{
  "bow": [
    {
      "rank": 1,
      "page_id": 50732483,
      "title": "List of cities founded by the Romans",
      "url": "https://en.wikipedia.org/wiki/List_of_cities_founded_by_the_Romans",
      "score": 0.3518531734723102
    }
  ],
  "lsa": [
    {
      "rank": 1,
      "page_id": 37772047,
      "title": "Felicior Augusto, melior Traiano",
      "url": "https://en.wikipedia.org/wiki/Felicior_Augusto,_melior_Traiano",
      "score": 0.73942004256181
    }
  ],
  "bm25": [
    {
      "rank": 1,
      "page_id": 1243432,
      "title": "Joseph Tainter",
      "url": "https://en.wikipedia.org/wiki/Joseph_Tainter",
      "score": 13.133878304616411
    }
  ]
}
```

---

## Pliki indeksu

Po zbudowaniu indeksu w `data/index/` pojawiają się:

| Plik | Model | Zawartość |
|---|---|---|
| `tfidf_matrix.npz` | BoW | Macierz TF-IDF (vocab × n\_docs), scipy CSR |
| `tfidf_vectorizer.pkl` | BoW, LSA | Dopasowany `TfidfVectorizer` (transformacja zapytań) |
| `lsa_vectors.npy` | LSA | Wektory LSA dokumentów (300 × n\_docs) |
| `svd_model.pkl` | LSA | Dopasowany `TruncatedSVD` (rzutowanie zapytań LSA) |
| `bm25_vectorizer.pkl` | BM25 | Dopasowany `BM25Vectorizer` (macierz wystąpień, IDF, długości dokumentów, słownik) |
| `doc_meta.pkl` | wszystkie | Metadane dokumentów: `page_id`, `title`, `url` |

`BM25Vectorizer` jest samowystarczalny — przechowuje wewnątrz korpus i wszystkie statystyki potrzebne do rankingu, więc BM25 nie potrzebuje osobnych plików z macierzą ani statystykami.

---
