import json


def load_json(filename):
    try:
        with open(filename) as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Warning: {filename} not found. Skipping.")
        return None


def main():
    word_frequencies = load_json("word_frequencies.json")
    unique_pages = load_json("unique_pages.json")
    longest_page = load_json("longest_page.json")

    lines = []
    lines.append("=" * 60)
    lines.append("Web Crawler Report")
    lines.append("=" * 60)

    # Unique pages
    lines.append("\nQuestion 1: Unique Pages")
    lines.append("-" * 40)
    if unique_pages is not None:
        lines.append(f"Total unique pages found: {len(unique_pages)}")
    else:
        lines.append("No data available.")

    # Longest page
    lines.append("\nQuestion 2: Longest Page")
    lines.append("-" * 40)
    if longest_page is not None:
        lines.append(f"URL: {longest_page['url']}")
        lines.append(f"Word count: {longest_page['count']}")
    else:
        lines.append("No data available.")

    # Top 50 words
    lines.append("\nQuestion 3: Top 50 Most Common Words")
    lines.append("-" * 40)
    if word_frequencies is not None:
        sorted_words = sorted(word_frequencies.items(), key=lambda x: x[1], reverse=True)
        for i, (word, count) in enumerate(sorted_words[:50], start=1):
            lines.append(f"{i:>2}. {word:<20} {count}")
    else:
        lines.append("No data available.")
