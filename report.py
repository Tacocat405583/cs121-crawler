import json
from urllib.parse import urlparse
from collections import defaultdict


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

    # Subdomains
    lines.append("\nQuestion 4: Subdomains")
    lines.append("-" * 40)
    if unique_pages is not None:
        subdomain_counts = defaultdict(int)
        for url in unique_pages:
            parsed = urlparse(url)
            netloc = parsed.netloc.lower()
            if ":" in netloc:
                netloc = netloc.split(":")[0]
            if netloc.endswith(".uci.edu") or netloc == "uci.edu":
                subdomain_counts[netloc] += 1
        sorted_subdomains = sorted(subdomain_counts.items(), key=lambda x: x[0])
        lines.append(f"Total unique subdomains found: {len(sorted_subdomains)}")
        for subdomain, count in sorted_subdomains:
            lines.append(f"{subdomain}, {count}")
    else:
        lines.append("No data available.")

    report = "\n".join(lines)

    with open("report.txt", "w") as f:
        f.write(report)
    print("Report saved to report.txt")


if __name__ == "__main__":
    main()
