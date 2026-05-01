from tokenizer import word_frequencies

# Exact duplicate
SEEN_PAGES = set()

# Near duplicate + config
FINGERPRINTS = {}
N = 3
NGRAM_MOD_VALUE = 4
THRESHOLD = 0.9

def partition_checksum(text: str, num_partitions: int = 2, width: int = 8) -> int:
    text_partitions = [0] * num_partitions
    for idx, char in enumerate(text):
        text_partitions[idx % num_partitions] += (ord(char) ^ (idx + 1)) * (idx + 1)
    
    parsed_hash = ""
    for i in range(num_partitions):
        parsed_hash += f"{text_partitions[i]:0{width}d}"
    
    return int(parsed_hash)
