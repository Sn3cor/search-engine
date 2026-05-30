import nltk
import re
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

nltk.download('stopwords')
nltk.download('punkt_tab')
STOP_WORDS = set(stopwords.words('english'))
stemmer = nltk.stem.PorterStemmer()


def tokenize_text(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    text = word_tokenize(text)
    text = [word for word in text if word not in STOP_WORDS]
    return text


def stem_words(words):
    return [stemmer.stem(word) for word in words]


def preprocess(text: str) -> list[str]:
    return stem_words(tokenize_text(text))

if __name__ == "__main__":
    text = "Hello, world! This is a test sentence running on a computer."
    print(tokenize_text(text))
    print(stem_words(tokenize_text(text)))
    print(preprocess(text))
    