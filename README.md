# search-engine

## Jakub Krupa

---

## Struktura projektu

```
simple-browser/
├── search-engine/
│   ├── crawler/
│   │   └── main.py          # Crawler BFS po kategoriach Wikipedii
│   ├── src/
│   │   ├── preprocessor.py  # Funckje tokenizacji i stemmingu korpusu
│   │   ├── indexer.py       # Budowanie indeksu (BoW z TF-IDF, BM25, LSA)
│   │   ├── test.py          # Skrypt do testowania modeli bez REST API
│   │   ├── api/
│   │   │   └── main.py      # REST API (FastAPI)
│   │   └── model/
│   │       ├── bow.py       # Model Bag of Words z TF-IDF
│   │       ├── bm25.py      # Model BM25
│   │       └── lsa.py       # Model LSA (Latent Semantic Analysis)
│   └── requirements.txt
└── frontend/                # Aplikacja kliencka
```

---

## Dataset
Do realizacji wyszukiarki wykorzystałem 100 000 artykułów z Wikipedii z kategorii Historia. Słownik ograniczyłem w kazdym modelu do 70 000 słów.


## "Crawler"

W zasadzie nie jest to prawdziwy crawler, chodzący po stronach i pobierający caly HTML, poniewaz wykorzystałem API udostępnione przez Wikipedię. Cały skrypt oparty jest o algorytm BFS. W przypadku natrafienia na stronę kategorii, pobierane są przez API podlinkowane strony z artykułami oraz kolejkowane są strony z kategoriami. Crawler umozliwia skonfigurowanie kategorii początkowej w postaci stringa `Category:<Kategoria>`, liczby artykułów do zapisania oraz głębokości kategorii, do której masymalnie zejdzie algorytm. Wykorzystałem BFSa, aby pobierać artykuły spokrewnione z początkową kategorią. Dodałem takze zabezpieczenia przed wpadnięciem w cykl przez zapamiętywanie odwiedzonych kategorii. Żaden z artykułów równiez nie zostanie pobrany dwukrotnie przez zapamiętywanie page_id pobranych artykułów.
Kazdy artykuł zostaje zapisany jako linijka w `search-engine/data/data.jsonl` w postaci:

```json
{
    "id": 00000
    "title": "Tytuł"
    "utl": "https://en.wikipedia.org/wiki/Artykuł"
    "text": "Tekst artykułu"
}
```

## Przetworzenie tekstu
Każdy vectorizer użyty w procesie indeksowania wykorzystuje funkcję `preprocess` z `search-engine/src/preprocessor.py`. Jej zadaniem jest normalizacja tekstu wejściowego, obejmująca konwersję na małe litery oraz usunięcie niepotrzebnych znaków. Dodatkowo filtrowane są powszechne słowa niewnoszące znaczenia semantycznego (stop words). Następnie przy pomocy algorytmu Porter Stemmer pozostałe tokeny sprowadzane są do rdzeni.

## Indeksowanie

Po zebraniu danych kazdy z modeli buduje potrzebne dla siebie obiekty i zapisuje je w do plików w katalogu `search-engine/data/index`

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
Dokumenty przetwarzane są przy uzyciu TfidfVectorizer'a do postaci wektorów kolumnowych z wagami TF-IDF (Term Frequency - Inverse Document Frequency). Dla kadzdego słowa w danym dokumencie liczone jest: 
```math
tfidf(t,d,D) = tf(t,d) \cdot idf(t,D)
```
gdzie:

$t$ - słowo (jego pozostałość po stemmingu),  

$d$ - dokument (jego pozostałość po stemmingu),

$D$ - zbiór wszystkich dokumentów (jego pozostałość po stemmingu),

$tf(t, d) = 1 + \ln(f_{t,d})$ - częstotliwość występowania słowa $t$ w dokumencie $d$; $f_{t,d}$ - liczba wystąpień słowa $t$ w dokumancie $d$,

$idf(t,D) = \ln\left(\frac{N + 1}{n_t + 1}\right) + 1$ - odwrotna częstotliwość występowania słowa $t$ w $N = |D|$ dokumentach; $n_t$ - liczba dokumentów zawierająca słowo $t$

W ten sam sposób przekształcany jest wektor zapytania. Podobieństwo liczone jest jako cosinus między wektorem zapytania a każdym werkotrem dokumentu w macierzy. 

Wynikiem jest $top_n=10$ dokumentów z największym podobieństwami.

### LSA (Latent Semantic Analysis)
Konstruowana jest macierz taka jak w modelu Bag of Words z TF-IDF, ale zostaje rozłozona na trzy macierze za pomocą dekompozycji SVD  a następnie przyblizona do rzędu 300 przy użyciu TruncatedSVD z paczki sklearn. Przy ładowaniu modelu do obsługi zapytań, kazdy wektor korpusu zostaje znormalizowany.

Zapytanie przekształcane jest najpierw przez TfidfVecotrizer, a następnie sprowadzane do tego samego wymiaru przez zapisany wcześniej model TruncatedSVD oraz zostaje znormalizowane. Podobieństwo, tak jak w modelu BoW jest liczone cosinusem kąta między wektora zapytania, a kazdym wektorem dokumentu w macierzy.

Wynikiem jest $top_n=10$ dokumentów z największymi podobieństwami.

### BM25
Do obliczania wag bm25 wykorystałem paczkę [`bm25-vectorizer`](https://pypi.org/project/bm25-vectorizer/) oraz wariant `bm25plus`. Dokumenty zostają przekształcone za pomocą BM25Vectorizer'a do postaci macierzy z obliczonymi wagami dla kazdego slowa w kazdym dokumencie zgodnie ze wzorem:
$$S(t, d) = idf(t) \cdot \left( \frac{f_{t,d} \cdot (k_1 + 1)}{f_{t,d} + k_1 \cdot \left(1 - b + b \cdot \frac{|d|}{avgdl}\right)} + \delta \right)$$
gdzie:

$idf(t,D) = \ln\left(\frac{N + 1}{n_t}\right)$ - odwrotna częstotliwość występowania słowa $t$ w $N = |D|$ dokumentach; $n_t$ - liczba dokumentów zawierająca słowo $t$;

$f_{t,d}$ - częstotliwość wystąpień słowa $t$ w dokumancei $d$,

$|d|$ - długość dokumentu $d$

$avgdl$ - średnia długość dokumentów w zbiorze

$k_1$ - parametr saturacji częstoliwości

$b$ -  parametr kary za długość dokumentu

$\delta$ - minimalna nagroda za obecność słowa

Zapytanie przekształcane jest do postaci wektora $q$ zliczającego liczbę wystąpień kazdego słowa kluczowego. Następnie obliczany jest wektor wyników $s$ jako iloczyn wektora zapytania i macierzy wag $W$
```math
s = qW
```
Wynik dla danego dokumentu $s_d$ jest iloczynem wektora $q$ oraz wektora kolumnowego dokumentu $w_d$:

```math
s_d = qw_d = \sum_{i=1}^{V} q_i W_{i,d}
```
Wynikiem jest $top_n=10$ dokumentów z największymi wagami

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

## Przykładowe zapytania 

Proste zapytanie: `the plague`

```bash
curl -X POST http://127.0.0.1:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "the plague", "top_n": 1}'
```

Przykładowa odpowiedź z $top_n = 1$

```json
Response body

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

Bardziej opisowe zapytanie: `terrible disease outbreak that killed a massive part of the population in europe`

```bash
curl -X POST http://127.0.0.1:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "terrible disease outbreak that killed a massive part of the population in europe", "top_n": 1}'
```

Przykładowa odpowiedź z $top_n = 1$


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

## Uruchomienie aplikacji klienckiej

```sh
cd frontend
npm install
npm run dev
```
