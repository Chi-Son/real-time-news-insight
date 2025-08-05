import feedparser

rss_url = "https://vnexpress.net/rss/kinh-doanh.rss"
feed = feedparser.parse(rss_url)

for entry in feed.entries:
    print(entry.title)
    print(entry.link)
    print(entry.published)
