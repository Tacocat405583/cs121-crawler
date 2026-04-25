import json

with open("word_frequencies.json") as f:
    data = json.load(f)

sorted_words = sorted(data.items(), key=lambda x: x[1],reverse=True)
for word, count in sorted_words[:50]:
    print(f"{word}: {count}")
