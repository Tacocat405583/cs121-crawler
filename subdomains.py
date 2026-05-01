import json
from urllib.parse import urlparse
from collections import defaultdict

def main():
    try:
        with open('unique_pages.json', 'r') as f:
            urls = json.load(f)
    except FileNotFoundError:
        print("Error: unique_pages.json not found.")
        return

    subdomain_counts = defaultdict(int)

    for url in urls:
        parsed = urlparse(url)
        # Extract the network location (domain) and make it lowercase
        netloc = parsed.netloc.lower()
        
        # Remove port if present (e.g., ics.uci.edu:8080 -> ics.uci.edu)
        if ':' in netloc:
            netloc = netloc.split(':')[0]
            
        # Check if it is a subdomain of uci.edu
        if netloc.endswith('.uci.edu') or netloc == 'uci.edu':
            subdomain_counts[netloc] += 1

    # Sort alphabetically by subdomain name
    sorted_subdomains = sorted(subdomain_counts.items(), key=lambda x: x[0])

    print(f"Total unique subdomains found: {len(sorted_subdomains)}\n")
    for subdomain, count in sorted_subdomains:
        print(f"{subdomain}, {count}")

if __name__ == '__main__':
    main()
