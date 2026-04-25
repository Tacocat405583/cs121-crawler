import sys


# O(n) where n is the number of characters in the string
def tokenize(string: str) -> list[str]:
    tokenz = []
    current_token = []

    for char in string:
        char = char.lower()
        if char.isalnum() and char.isascii():
            current_token.append(char)
        else:
            if current_token:
                tokenz.append("".join(current_token))
                current_token = []

    if current_token:
        tokenz.append("".join(current_token))

    return tokenz


# O(n) where n is the number of characters in the string, yields one token at a time for RAM
def tokenize_stream(string: str):
    current_token = []

    for char in string:
        char = char.lower()
        if char.isalnum() and char.isascii():
            current_token.append(char)
        else:
            if current_token:
                yield "".join(current_token)
                current_token = []

    if current_token:
        yield "".join(current_token)


# O(n) where n is the number of tokens in the list
def compute_word_frequencies(tokens: list[str])->dict[str,int]:
    totals = {}

    for token in tokens:
        if token in totals:
            totals[token]+=1
        else:
            totals[token] = 1

    return totals


# O(n log n) where n is the number of unique tokens, due to sorting
def print_frequencies(frequencies:dict[str,int])->None:

    desc_sorted = {k: v for k, v in sorted(frequencies.items(), key=lambda item: (-item[1], item[0]))}# sorted is nlogn

    
    for token,freq in desc_sorted.items():
        print(f"{token} -> {freq}")


def main():
    tokens = tokenize(sys.argv[1])
    freqs = compute_word_frequencies(tokens)
    print_frequencies(freqs)


if __name__ == "__main__":
    main()
