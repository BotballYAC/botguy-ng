try:
    import feedparser
except:
    from . import feedparser3k as feedparser
import threading
from time import sleep

class RssPoller(threading.Thread):
    def __init__(self, feed, callback, poll_time=120):
        super(RssPoller, self).__init__()
        self.daemon = True
        self.feed_url = feed
        self.callback = callback
        self.poll_time = poll_time
        self.start()
    
    def run(self):
        self.feed = feedparser.parse(self.feed_url)
        self.id_set = set([e.id for e in self.feed.entries])
        while True:
            sleep(self.poll_time)
            self.poll()
    
    def poll(self):
        print(("Polling " + self.feed_url))
        parse_kwargs = {}
        if hasattr(self.feed, "modified"):
            parse_kwargs["modified"] = self.feed.modified
        if hasattr(self.feed, "etag"):
            parse_kwargs["etag"] = self.feed.etag
        self.feed = feedparser.parse(self.feed_url, **parse_kwargs)
        
        if len(self.feed.entries) > 0:
            for e in self.feed.entries:
                if e.id not in self.id_set:
                    print("New feed item")
                    self.callback(e)
                    self.id_set.add(e.id)
