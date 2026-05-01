from tokenizer import compute_word_frequencies

#partition checksum config
NUM_PARTITIONS = 2
WIDTH = 8

# Exact duplicate
SEEN_PAGES = set()

# Near duplicate + config
def bit_length(n: int) -> int:
    length = 0
    while n > 0:
        n >>= 1
        length += 1
    return length

SIMPRINTS_SET = {}
SIMHASH_BITS = bit_length(int("9" * (NUM_PARTITIONS * WIDTH)))
THRESHOLD = 0.9


def partition_checksum(text: str) -> int:
    text_partitions = [0] * NUM_PARTITIONS
    for idx, char in enumerate(text):
        text_partitions[idx % NUM_PARTITIONS] += (ord(char) ^ (idx + 1)) * (idx + 1)
    
    parsed_hash = ""
    for i in range(NUM_PARTITIONS):
        parsed_hash += f"{text_partitions[i]:0{WIDTH}d}"
    
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

def simhash(tokens: list[str]) -> int:
    # 1: process doc into a set of features with assoc weights
    word_weights = compute_word_frequencies(tokens)
    vector = [0] * SIMHASH_BITS
    for word, weight in word_weights.items():
        # generate a hash value for each word
        word_hash = partition_checksum(word)
        #update components by adding the weight for which corresponding bit
        for i in range(SIMHASH_BITS):
            if (word_hash >> i) & 1:
                vector[i] += weight
            else:
                vector[i] -= weight
    # gen fingeprint by setting ith bit to 1 if pos else 0
    fingerprint = 0
    for i in range(SIMHASH_BITS):
        if vector[i] > 0:
            fingerprint |= (1 << i)
    return fingerprint

#simhash similarity 
# s_(a,b) = sigma_n([1 if hashA_i == hashB_i else 0] * 1/b

def simhash_similarity(hashA: int, hashB: int):
    bit_count = 0
    for i in range(SIMHASH_BITS):
        if ((hashA >> i) & 1) == ((hashB >> i) & 1):
            bit_count += 1
    
    return bit_count / SIMHASH_BITS

def is_near_duplicate(tokens: list[str], url: str) -> bool:
    sim_print = simhash(tokens)
    for past_print in SIMPRINTS_SET.values():
        if simhash_similarity(sim_print, past_print):
            return True
    #no matches in set of sim_prints
    SIMPRINTS_SET[url] = sim_print
    return False
