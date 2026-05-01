from tokenizer import word_frequencies

# Exact duplicate
SEEN_PAGES = set()

# Near duplicate + config
FINGERPRINTS = {}
BITS = 64 #simhash bits
THRESHOLD = 0.9

def partition_checksum(text: str, num_partitions: int = 2, width: int = 8) -> int:
    text_partitions = [0] * num_partitions
    for idx, char in enumerate(text):
        text_partitions[idx % num_partitions] += (ord(char) ^ (idx + 1)) * (idx + 1)
    
    parsed_hash = ""
    for i in range(num_partitions):
        parsed_hash += f"{text_partitions[i]:0{width}d}"
    
    return int(parsed_hash)

def is_exact_duplicate(text: str) -> bool:
    page_checksum = partition_checksum(text)
    if page_checksum in SEEN_PAGES:
        return True
    else:
        SEEN_PAGES.add(page_checksum)
        return False

#def compute_word_frequencies(tokens: list[str])->dict[str,int]:
#   totals = {}
#
#    for token in tokens:
#        if token in totals:
#            totals[token]+=1
#        else:
#            totals[token] = 1
#
#    return totals

def simhash(text: str) -> int:
    # 1: process doc into a set of features with assoc weights
    word_weights = compute_word_frequencies(text)
    vector = [0] * BITS
    for word, weight in word_weights.items():
        # generate a hash value for each word
        word_hash = partition_checksum(word)
            #update components by adding the weight for which corresponding bit
            for i in range(BITS):
                if (word_hash >> i) & 1:
                    vector[i] += weight
                else:
                    vector[i] -= weight
    # gen fingeprint by setting ith bit to 1 if pos else 0
    fingerprint = 0
    for i in range(BITS):
        if vector[i] > 0:
            fingerprint |= (1 << i)
    return fingerprint