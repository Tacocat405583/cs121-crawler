from bs4 import BeautifulSoup
from tokenizer import tokenizer

# Exact duplicate
HASHES = set()

# Near duplicate + config
FINGERPRINTS = {}
N = 3
NGRAM_MOD_VALUE = 4
THRESHOLD = 0.9