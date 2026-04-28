import re
import atexit
import json
import warnings
import hashlib
from urllib.parse import urljoin, urldefrag, urlsplit, parse_qs

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

from tokenizer import tokenize, compute_word_frequencies

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


# English stop words to exclude from frequency counts
STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an",
    "and", "any", "are", "aren't", "as", "at", "be", "because", "been",
    "before", "being", "below", "between", "both", "but", "by", "can't",
    "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't",
    "doing", "don't", "down", "during", "each", "few", "for", "from",
    "further", "get", "got", "had", "hadn't", "has", "hasn't", "have",
    "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here",
    "here's", "hers", "herself", "him", "himself", "his", "how", "how's",
    "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't",
    "it", "it's", "its", "itself", "let's", "me", "more", "most", "mustn't",
    "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only",
    "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own",
    "same", "shan't", "she", "she'd", "she'll", "she's", "should",
    "shouldn't", "so", "some", "such", "than", "that", "that's", "the",
    "their", "theirs", "them", "themselves", "then", "there", "there's",
    "these", "they", "they'd", "they'll", "they're", "they've", "this",
    "those", "through", "to", "too", "under", "until", "up", "very", "was",
    "wasn't", "we", "we'd", "we'll", "we're", "we've", "were", "weren't",
    "what", "what's", "when", "when's", "where", "where's", "which", "while",
    "who", "who's", "whom", "why", "why's", "will", "with", "won't", "would",
    "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your",
    "yours", "yourself", "yourselves",
}

# Only crawl URLs whose netloc ends with one of these
ALLOWED_DOMAINS = (
    ".ics.uci.edu",
    ".cs.uci.edu",
    ".informatics.uci.edu",
    ".stat.uci.edu"
)

# Accumulated word counts across all crawled pages (stop words excluded)
WORD_FREQUENCIES = {}

# Set of unique defragmented URLs seen so far
UNIQUE_PAGES = set()

#Set of unique hashes
HASHES = set()

# Tracks the page with the most words: {"url": ..., "count": ...}
LONGEST_PAGE = {"url": "", "count": 0}

# Pages with fewer tokens than this are considered low information and skipped
LOW_INFO_THRESHOLD = 50

# These domains are leading to nothing usefull
BLOCKED_SUBDOMAINS = {
    "swiki.ics.uci.edu",
    "wiki.ics.uci.edu",
    "helpdesk.ics.uci.edu",
}


def save_data():
    # Called automatically on exit (including Ctrl+C) via atexit
    with open("word_frequencies.json", "w") as f:
        json.dump(WORD_FREQUENCIES, f)
    with open("unique_pages.json", "w") as f:
        json.dump(list(UNIQUE_PAGES), f)
    with open("longest_page.json", "w") as f:
        json.dump(LONGEST_PAGE, f)

atexit.register(save_data)


def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]


def extract_next_links(url, resp) -> list:
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content

    links = []

    # Skip pages that didn't load successfully
    if resp.status != 200 or not resp.raw_response:
        return links

    # Skip pages over 10MB to avoid memory issues and low-value content
    if len(resp.raw_response.content) > 10000000:
        return links

    soup = BeautifulSoup(resp.raw_response.content, "lxml")

    # Extract visible text and count word frequencies for this page
    text = soup.get_text()
    tokens = tokenize(string=text)


    # Skip low information pages (login pages, empty pages, redirects, etc.)
    if len(tokens) < LOW_INFO_THRESHOLD:
        return links
    
    ###LETS WORK ON DUPLICATE DETECTION ---- TEST
    hash_object = hashlib.sha256(text.encode())
    hex_dig = hash_object.hexdigest()
    if hex_dig in HASHES:
        return links
    else:
        HASHES.add(hex_dig)

    # NEAR DUPLICATE DETECTION TEST - find near duplicates of a document D -> O(N) comparisons
    # We should have some threshold

    # Update longest page if this page has more words than the current max
    if len(tokens) > LONGEST_PAGE["count"]:
        LONGEST_PAGE["url"] = urldefrag(url)[0] #dont do [1] thats the fragment
        LONGEST_PAGE["count"] = len(tokens)

    words = compute_word_frequencies(tokens=tokens)

    # Track this page as visited (fragment stripped so #section variants collapse)
    UNIQUE_PAGES.add(urldefrag(url)[0])

    # Merge this page's word counts into the global tally, skipping stop words
    for word, count in words.items():
        if word not in STOP_WORDS:
            WORD_FREQUENCIES[word] = WORD_FREQUENCIES.get(word, 0) + count

    # Collect all anchor hrefs, resolve to absolute URLs, strip fragments
    for tag in soup.find_all("a"):
        href = tag.get("href")
        if href:
            absolute = urljoin(url, href)
            absolute = urldefrag(absolute)[0]
            links.append(absolute)

    return links


# URL Parts
# https://www.geeksforgeeks.org:80/array-data-structure?ref=home-articlecards#what-is-array
# |_____|  |__________________|  |__| |________________| | |__________________| |__________|
# Scheme      Domain Name        Port  Path to the File  ?     Parameters        Fragment
#                |___________________________|
#                           Authority


def is_valid(url):
    # Decide whether to crawl this url or not.
    # If you decide to crawl it, return True; otherwise return False.
    try:
        parsed = urlsplit(url)

        # Only follow http/https links
        if parsed.scheme not in {"http", "https"}:
            return False

        # Reject URLs outside the allowed domains
        if not any(parsed.netloc.endswith(domain) for domain in ALLOWED_DOMAINS):
            return False
        
        if parsed.netloc in BLOCKED_SUBDOMAINS:
            return False
        
        # This is to skip pages with insufficient access in doku.php
        if "/group:support" in parsed.path:
            return False

        # Avoid paginated archives beyond page 20 (low-value duplicate content)
        page_match = re.search(r"/page/(\d+)", parsed.path)
        if page_match and int(page_match.group(1)) > 20:
            return False

        # Block WordPress date archive URLs (e.g. /2019, /2019/04, /2019/04/04) for acoi
        if re.search(r"/\d{4}(/\d{2}){0,2}$", parsed.path):
            return False

        # Long query strings or repeated parameters indicate a URL trap
        if len(parsed.query) > 200:
            return False
        #appeared more than once in the query string
        if any(len(v) > 1 for v in parse_qs(parsed.query).values()):
            return False

        # Block Apache directory listing sort variants (same content, different order)
        if "C=" in parsed.query and "O=" in parsed.query:
            return False

        # Block DokuWiki action/index queries that were pissing me off
        if "/doku.php" in parsed.path:
            bad_params = ("do=", "idx=")
            query = parsed.query.lower()
            if any(p in query for p in bad_params):
                return False

        # Reject static asset and binary file extensions
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|pps|ppsx|doc|docx|xls|xlsx|names" #pptx added
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print("TypeError for ", parsed)
        raise
