from tokenizer import tokenizer

# Exact duplicate
SEEN_PAGES = set()

# Near duplicate + config
FINGERPRINTS = {}
N = 3
NGRAM_MOD_VALUE = 4
THRESHOLD = 0.9