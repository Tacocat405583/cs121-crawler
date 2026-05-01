from utils import get_logger
from crawler.frontier import Frontier
from crawler.worker import Worker

class Crawler(object):
    def __init__(self, config, restart, frontier_factory=Frontier, worker_factory=Worker):
        self.config = config
        self.logger = get_logger("CRAWLER")
        self.frontier = frontier_factory(config, restart)
        self.workers = list()
        self.worker_factory = worker_factory

    def start_async(self):
        self.workers = [
            self.worker_factory(worker_id, self.config, self.frontier)
            for worker_id in range(self.config.threads_count)]
        for worker in self.workers:
            worker.start()

    def start(self):
        self.start_async()
        self.join()

    def join(self):
        try:
            for worker in self.workers:
                worker.join()
        except KeyboardInterrupt:
            print("\n[Ctrl+C detected] Waiting for the current download to finish so we can safely pause.")
            for worker in self.workers:
                worker.stop_flag = True
            for worker in self.workers:
                worker.join()
            print("Successfully paused, you can safely resume later.")
        finally:
            if hasattr(self, 'frontier') and hasattr(self.frontier, 'save'):
                self.frontier.save.close()
