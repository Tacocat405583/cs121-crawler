import re
import atexit
import json
from urllib.parse import urlparse,urljoin,urldefrag,urlsplit
from bs4 import BeautifulSoup
from tokenizer import tokenize,compute_word_frequencies

#Stop Words

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

# Allowed Domains

ALLOWED_DOMAINS = (
    ".ics.uci.edu",
    "cs.uci.edu",
    ".informatics.uci.edu/",
    ".stat.uci.edu/"
)

#Page Length  Max

WORD_FREQUENCIES = {}


def save_frequencies():
    with open("word_frequencies.json", "w") as f:
        json.dump(WORD_FREQUENCIES, f)

atexit.register(save_frequencies)


def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp)->list:

    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content



    links = []

    #if over 10 mb we dont scan it for now, I think this works rn
    if len(resp.raw_response.content) > 10000000:
        return False

    if resp.status != 200 or not resp.raw_response:
        return links
    
    soup = BeautifulSoup(resp.raw_response.content, "lxml")

    text = soup.get_text()
    tokens = tokenize(string=text)
    words = compute_word_frequencies(tokens=tokens)
    
    for word, count in words.items():
        if word not in STOP_WORDS:
            WORD_FREQUENCIES[word] = WORD_FREQUENCIES.get(word, 0) + count



    for tag in soup.find_all("a"):
        href = tag.get("href")
        if href:
            absolute = urljoin(url, href)
            absolute = urldefrag(absolute)[0] #supposed to remove frags, does not seem to wrk rn
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
    # There are already some conditions that return False.
    try:
        parsed = urlsplit(url) # return named tuple 
        if parsed.scheme not in set(["http", "https"]):
            return False
        allowed = False

        #If domain ends with allowed then pass
        for domain in ALLOWED_DOMAINS:
            if parsed.netloc.endswith(domain):
                allowed = True
                break        
        if not allowed:
            return False
        

        #checking page count 
        if parsed.path.startswith("/page"):
            return False
        

        #This is to stop teh doku.php do queries
        #NEW ADDITION TESTING
        if "/doku.php" in parsed.path:
            bad_stuff = ("do=","idx=")
            query = parsed.query.lower() #DO -> do
            if any(bad in query for bad in bad_stuff):
                return False
        
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise
