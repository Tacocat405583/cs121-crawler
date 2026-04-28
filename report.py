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
