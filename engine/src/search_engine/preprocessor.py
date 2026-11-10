import re
from functools import lru_cache

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

for pkg, path in [
    ("stopwords", "corpora/stopwords"),
    ("punkt_tab", "tokenizers/punkt_tab"),
]:
    try:
        nltk.data.find(path)
    except LookupError:
        nltk.download(pkg, quiet=True)

STOP_WORDS = set(stopwords.words("english"))
cached_stem = lru_cache(maxsize=2**18)(nltk.stem.PorterStemmer().stem)


def preprocess(text: str) -> list[str]:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    words = word_tokenize(text)
    words = [word for word in words if word not in STOP_WORDS]
    return [cached_stem(word) for word in words]


def main():
    text = "Hello, world! This is a test sentence running on a computer."
    print(preprocess(text))


if __name__ == "__main__":
    main()
