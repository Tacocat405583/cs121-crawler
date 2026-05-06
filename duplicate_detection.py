from tokenizer import compute_word_frequencies

#partition checksum config
NUM_PARTITIONS = 2
WIDTH = 8
THRESHOLD = 0.9


def partition_checksum(text: str) -> int:
    text_partitions = [0] * NUM_PARTITIONS
    for idx, char in enumerate(text):
        text_partitions[idx % NUM_PARTITIONS] += (ord(char) ^ (idx + 1)) * (idx + 1)
    
    parsed_hash = ""
    for i in range(NUM_PARTITIONS):
        parsed_hash += f"{text_partitions[i]:0{WIDTH}d}"
    
    return int(parsed_hash)

def is_exact_duplicate(text: str, visited_pages: set) -> bool:
    page_checksum = partition_checksum(text)
    if page_checksum in visited_pages:
        return True
    else:
        visited_pages.add(page_checksum)
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
    vector = {}
    for word, weight in word_weights.items():
        # generate a hash value for each word
        word_hash = partition_checksum(word)
        #update components by adding the weight for which corresponding bit
        for i in range(word_hash.bit_length()):
            if (word_hash >> i) & 1:
                vector[i] += vector.get(i, 0) + weight
            else:
                vector[i] -= vector.get(i, 0) - weight
    # gen fingeprint by setting ith bit to 1 if pos else 0
    fingerprint = 0
    for i, v in vector.items():
        if v > 0:
            fingerprint |= (1 << i)
    return fingerprint

#simhash similarity 
# s_(a,b) = sigma_n([1 if hashA_i == hashB_i else 0] * 1/b

def simhash_similarity(hashA: int, hashB: int):
    total_bits = max(hashA.bit_length(), hashB.bit_length(), 1)
    bit_count = 0
    for i in range(total_bits):
        if ((hashA >> i) & 1) == ((hashB >> i) & 1):
            bit_count += 1
    
    return bit_count / total_bits

def is_near_duplicate(tokens: list[str], url: str, simprints_set: dict) -> bool:
    sim_print = simhash(tokens)
    for past_print in simprints_set.values():
        if simhash_similarity(sim_print, past_print) >= THRESHOLD:
            return True
    #no matches in set of sim_prints
    simprints_set[url] = sim_print
    return False
