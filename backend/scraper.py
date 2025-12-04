import feedparser
import requests
from bs4 import BeautifulSoup
from newspaper import Article
import time

def get_full_text(url):
    """Extracts full text from a URL using newspaper3k."""
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.text
    except Exception as e:
        print(f"Error extracting text from {url}: {e}")
        return ""

def scrape_bbc():
    """Scrapes BBC World News via RSS."""
    print("Scraping BBC...")
    feed_url = "http://feeds.bbci.co.uk/news/world/rss.xml"
    feed = feedparser.parse(feed_url)
    articles = []
    for entry in feed.entries[:5]:  # Limit to 5 for now
        full_text = get_full_text(entry.link)
        articles.append({
            "title": entry.title,
            "link": entry.link,
            "summary": entry.summary, # Keep RSS summary as fallback/metadata
            "full_text": full_text if full_text else entry.summary, # Use summary if full text fails
            "source": "BBC",
            "published": entry.published
        })
    return articles

def scrape_cnn():
    """Scrapes CNN World News via RSS."""
    print("Scraping CNN...")
    feed_url = "http://rss.cnn.com/rss/edition_world.rss"
    feed = feedparser.parse(feed_url)
    articles = []
    for entry in feed.entries[:5]:
        # CNN RSS summaries are often short or contain HTML
        summary = BeautifulSoup(entry.summary, "html.parser").get_text() if 'summary' in entry else ""
        full_text = get_full_text(entry.link)
        articles.append({
            "title": entry.title,
            "link": entry.link,
            "summary": summary,
            "full_text": full_text if full_text else summary,
            "source": "CNN",
            "published": entry.published if 'published' in entry else ""
        })
    return articles

def scrape_reuters():
    """Scrapes Reuters World News via HTML."""
    print("Scraping Reuters...")
    url = "https://www.reuters.com/world/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, "html.parser")
        articles = []
        
        # Reuters structure changes often, looking for common article containers
        for item in soup.select('li[data-testid="story-card"]', limit=5):
             title_elem = item.select_one('a[data-testid="Heading"]')
             if title_elem:
                title = title_elem.get_text()
                link = "https://www.reuters.com" + title_elem['href']
                full_text = get_full_text(link)
                
                articles.append({
                    "title": title,
                    "link": link,
                    "summary": title, # Placeholder
                    "full_text": full_text if full_text else title,
                    "source": "Reuters",
                    "published": "Today" # Placeholder
                })
        
        if not articles:
            # Fallback: try generic link search if specific selectors fail
             for link in soup.select('h3 a', limit=5):
                href = link['href']
                if not href.startswith('http'):
                    href = "https://www.reuters.com" + href
                
                full_text = get_full_text(href)
                articles.append({
                    "title": link.get_text().strip(),
                    "link": href,
                    "summary": "",
                    "full_text": full_text,
                    "source": "Reuters",
                    "published": ""
                })

        return articles
    except Exception as e:
        print(f"Error scraping Reuters: {e}")
        return []

def scrape_all_news():
    all_news = []
    all_news.extend(scrape_bbc())
    all_news.extend(scrape_cnn())
    all_news.extend(scrape_reuters())
    return all_news

if __name__ == "__main__":
    news = scrape_all_news()
    for article in news:
        print(f"[{article['source']}] {article['title']}")
        print(f"Link: {article['link']}")
        print(f"Text Length: {len(article.get('full_text', ''))}")
        print("-" * 20)
