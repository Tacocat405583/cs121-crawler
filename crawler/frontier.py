import os
import glob
import shelve
import time

from threading import Condition

from urllib.parse import urldefrag, urlsplit

from utils import get_logger, get_urlhash, normalize
from scraper import is_valid, UNIQUE_PAGES

from collections import deque, defaultdict

POLITENESS_DELAY = 0.5


class Frontier(object):
    def __init__(self, config, restart):
        self.logger = get_logger("FRONTIER")
        self.config = config

        self.domain_queues = defaultdict(deque)
        self.domain_last_hit = {}
        self.condition = Condition()
        self.active_count = 0
        
        existing_files = glob.glob(self.config.save_file + "*")
        if not existing_files and not restart:
            # Save file does not exist, but request to load save.
            self.logger.info(
                f"Did not find save file {self.config.save_file}, "
                f"starting from seed.")
        elif existing_files and restart:
            # Save file exists, but request to start from seed — delete all shelve files.
            self.logger.info(
                f"Found save file {self.config.save_file}, deleting it.")
            for f in existing_files:
                os.remove(f)
        # Load existing save file, or create one if it does not exist.
        self.save = shelve.open(self.config.save_file)
        if restart:
            for url in self.config.seed_urls:
                self.add_url(url)
        else:
            # Set the frontier state with contents of save file.
            self._parse_save_file()
            if not self.save:
                for url in self.config.seed_urls:
                    self.add_url(url)

    def _parse_save_file(self):
        ''' This function can be overridden for alternate saving techniques. '''
        
        total_count = len(self.save)
        tbd_count = 0
        repaired_count = 0
        
        # list() is required because we are modifying self.save during iteration
        for urlhash, (url, completed) in list(self.save.items()):
            if completed:
                defrag_url = urldefrag(url)[0]
                if defrag_url not in UNIQUE_PAGES:
                    # Data was lost in a crash. Revert to incomplete so it gets re-crawled
                    self.save[urlhash] = (url, False)
                    completed = False
                    repaired_count += 1
                    
            if not completed and is_valid(url):
                self.domain_queues[self._get_domain(url)].append(url) # changed since we are using deq now
                tbd_count += 1
                
        if repaired_count > 0:
            self.save.sync()
            self.logger.warning(f"Auto-repaired {repaired_count} lost URLs from previous catastrophic crash.")
            
        self.logger.info(
            f"Found {tbd_count} urls to be downloaded from {total_count} "
            f"total urls discovered.")

    def get_tbd_url(self):
        """Finds a domain thats ready, sleeps if nothing ready, returns None when truly done"""
        with self.condition:## better to use context managers
            while True:
                now = time.time()
                best_domain = None #which domain to give to worker
                min_wait = float('inf')

                for domain, q in self.domain_queues.items():
                    if not q: #skip empty buckets first.
                        continue
                    elapsed = now - self.domain_last_hit.get(domain, 0) # how long since we last hit this domain. 
                    wait = max(0.0, POLITENESS_DELAY - elapsed)
                    if wait == 0.0:
                        best_domain = domain
                        min_wait = 0.0
                        break
                    elif wait < min_wait:
                        min_wait = wait
                        best_domain = domain

                if best_domain is None: # when every domain queue is empty
                    if self.active_count == 0:
                        self.condition.notify_all() #every sleeps 
                        return None
                    self.condition.wait(timeout=POLITENESS_DELAY) # releases lock and sleeps
                    continue

                if min_wait > 0.0: #found best domain but cooldown so we sleep x wait long
                    self.condition.wait(timeout=min_wait)
                    continue

                
                # pop the next URL from the front of this domain's queue (FIFO)
                url = self.domain_queues[best_domain].popleft()

                # record when we last hit this domain to enforce 500ms cooldown
                self.domain_last_hit[best_domain] = time.time()

                # one more worker is now mid-crawl, prevents premature shutdown
                self.active_count += 1
                
                return url

    def _get_domain(self, url):
        return urlsplit(url).netloc

    def add_url(self, url):
        url = normalize(url)
        # strip query string — only domain + path matter for uniqueness
        url = urlsplit(url)._replace(query="", fragment="").geturl()
        urlhash = get_urlhash(url)
        # NEW: wrap in condition lock so two threads can't add the same URL simultaneously.
        # Appends to the domain's deque instead of the old flat list.
        # notify_all() wakes any worker sleeping in get_tbd_url waiting for new URLs.
        with self.condition:
            if urlhash not in self.save:
                self.save[urlhash] = (url, False)
                self.save.sync()
                self.domain_queues[self._get_domain(url)].append(url)
                self.condition.notify_all()

    def mark_url_complete(self, url):
        urlhash = get_urlhash(url)
        # NEW: wrap in condition lock so active_count stays consistent across threads.
        # active_count -= 1 tells get_tbd_url that one fewer worker is mid-download,
        # allowing it to return None and shut down when queues are truly empty.
        # notify_all() wakes workers that may be waiting on the empty-queue check.
        with self.condition:
            if urlhash not in self.save:
                self.logger.error(
                    f"Completed url {url}, but have not seen it before.")
            self.save[urlhash] = (url, True)
            self.save.sync()
            self.active_count -= 1
            self.condition.notify_all()
