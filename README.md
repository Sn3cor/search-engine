# search-engine


## Dataset
Do realizacji wyszukiarki wykorzystałem 100 000 artykułów z Wikipedii z kategorii Historia. Słownik ograniczyłem w kazdym modelu do 70 000.

<!-- --- -->

<!-- ## Struktura projektu

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

--- -->

## Crawler

W zasadzie nie jest to prawdziwy crawler, chodzący po stronach i zapisujący caly HTML, poniewaz wykorzystałem api udostępnione przez Wikipedię. 
Cały skrypt oparty jest o algorytm BFS i odwiedzanie kolejnych stron z artykułami lub kategoriami. W przypadku natrafienia na stronę kategorii, zbierane są podlinkownae tam strony z artykułami oraz kolejne strony z kategoriami. 
Crawler umozliwia skonfigurowanie kategorii początkowej w postaci stringa `Category:<Kategoria>`, ilości artykułów do zapisania oraz głębokości, do której masymalnie zejdzie algorytm. BFS został uzyty, poniewaz istnieje ryzyko wystąpienia cyklu, np. na głębokości 4 wystąpi strona kategorii z odnośnikiem do kategorii początkowej.
Kazdy artykuł zostaje zapisany jako linijka w `search-engine/data/data.jsonl` w postaci:

```json
{
    "id": 00000
    "title": "Tytuł"
    "utl": "https://en.wikipedia.org/wiki/Artykuł"
    "text": "Tekst artykułu"
}
```
## Indeksowanie

Po zebraniu danych kazdy z modeli buduje potrzebne dla siebie obiekty i zapisuje je w do plików w katalogu `seatch-engine/data/index`

| Plik | Model | Zawartość |
|---|---|---|
| `tfidf_matrix.npz` | BoW | Rzadka macierz TF-IDF |
| `tfidf_vectorizer.pkl` | BoW, LSA | Dopasowany `TfidfVectorizer` (transformacja zapytań) |
| `lsa_matrix.npy` | LSA | Gęsta macierz LSA |
| `svd_model.pkl` | LSA | Dopasowany `TruncatedSVD` (rzutowanie zapytań dla LSA) |
| `bm25_matrix.npz` | BM25 | Macierz wag BM25+ |
| `bm25_vectorizer.pkl` | BM25 | Dopasowany `BM25Vectorizer` |
| `doc_meta.pkl` | wszystkie | Metadane dokumentów: `page_id`, `title`, `url` |

## Modele wyszukiwania

### Bag of Words z TF-IDF
Korpusy i zapytania reprezentowane są jako wektory TF-IDF w macierzy przy uzyciu TfidfVectorizer'a, gdzie dla kadzdego słowa w danym dokumencie liczone jest: $$tfidf(t,d,D) = tf(t,d) \cdot idf(t,D) $$ 
gdzie:

$t$ - słowo (jego pozostałość po stemmingu),  

$d$ - dokument (jego pozostałość po stemmingu),

$D$ - zbiór wszystkich dokumentów (jego pozostałość po stemmingu),

$tf(t, d) = 1 + \ln(f_{t,d})$ - częstotliwość występowania słowa $t$ w dokumencie $d$; $f_{t,d}$ - częstotliwość wystąpień słowa $t$ w dokumancei $d$,

$idf(t,D) = \ln\left(\frac{N + 1}{n_t + 1}\right) + 1$ - odwrotna częstotliwość występowania słowa $t$ w $N = |D|$ dokumentach; $n_t$ - ilość dokumentów zawierająca słowo $t$

W ten sam sposób przekształcany jest wektor zapytania. Podobieństwo liczone jest jako odległość cosinusowa między wektorem zapytania a każdym dokumentem w macierzy. 

Wynikiem jest $top_n=10$ dokumentów z największym podobieństwem (największym cosinusem kąta/najmniejszym kątem między wektorami)

### LSA (Latent Semantic Analysis)
Konstruowana jest macierz taka jak w modelu Bag of Words z TF-IDF, ale zostaje rozłozona na trzy macierze za pomocą dekompozycji SVD  a następnie przyblizona do rzędu 300 przy użyciu TruncatedSVD z paczki sklearn. Przy ładowaniu modelu do obsługi zapytań, kazdy wektor zostaj znormalizowany.

Zapytanie przekształcane jest najpierw przez TfidfVecotrizer, a następnie do tego samego wymiaru przez zapisany wcześniej model TruncatedSVD. Podobieństwo, tak jak w modelu BoW jest liczone odległością cosinusową wektora zapytania od kazdego wektora w macierzy z dokumentami. Przed porównaniem wektor zostaje znormalizowany.

Wynikiem jest $top_n=10$ dokumentów z największym podobieństwem (największym cosinusem kąta/najmniejszym kątem między wektorami)

### BM25
Do obliczania wag bm25 wykorystałem paczkę [`bm25-vectorizer`](https://pypi.org/project/bm25-vectorizer/) oraz wariant `bm25plus`. Dokumenty zostają przekształcone za pomocą BM25Vectorizer'a do postaci macierzy z obliczonymi wagami dla kazdego slowa w kazdym dokumencie zgodnie ze wzorem:
$$S(t, d) = idf(t) \cdot \left( \frac{f_{t,d} \cdot (k_1 + 1)}{f_{t,d} + k_1 \cdot \left(1 - b + b \cdot \frac{|d|}{avgdl}\right)} + \delta \right)$$
gdzie:

$idf(t,D) = \ln\left(\frac{N + 1}{n_t}\right)$ - odwrotna częstotliwość występowania słowa $t$ w $N = |D|$ dokumentach; $n_t$ - ilość dokumentów zawierająca słowo $t$;

$f_{t,d}$ - częstotliwość wystąpień słowa $t$ w dokumancei $d$,

$|d|$ - długość dokumentu $d$

$avgdl$ - średnia długość dokumentów w zbiorze

$k_1$ - parametr saturacji częstoliwości

$b$ -  parametr kary za długość dokumentu

$\delta$ - minimalna nagroda za obecność słowa

Zapytanie jest przekształcany do postaci wektora $q$ zliczającego liczbę wystąpień kazdego słowa kluczowego, a następnie wykonywane jest mnozenie tego wektora z macierzą $W$ wag BM25+. Wektorem wynikowym $s$:
$$s = qW$$
Wynik dla danego dokumentu $s_d$ jest iloczynem wektora $q$ oraz wektora kolumnowego dokumentu $w_i$:
$$s_d = qw_d = \sum_{i=1}^{V} q_i W_{i,d} $$

Następnie z wektora $s$ wyciągane są $top_n=10$ dokumenty z największymi wagami jako wynik.

---



## Instalacja wymaganych paczek

```bash
cd search-engine
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Uruchomienie

### 1. Zbieranie danych (crawler)

```bash
cd search-engine
python crawler/main.py
```

Domyślnie pobiera do 100 000 artykułów z kategorii `Category:History` z głębokością 5.

### 2. Budowanie indeksu

Indeks budowany jest automatycznie przy pierwszym uruchomieniu API. Można też zbudować go wcześniej ręcznie:

```bash
cd search-engine
python -m src.indexer
```

### 3. Uruchomienie API

```bash
cd search-engine
fastapi dev src/api/main.py
```

Serwer będzie dostępny pod `http://127.0.0.1:8000`.

### 4. Zapytanie do API

```bash
curl -X POST http://127.0.0.1:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Roman Empire collapse", "top_n": 1}'
```

Przykładowa odpowiedź z $top_n = 1$

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
