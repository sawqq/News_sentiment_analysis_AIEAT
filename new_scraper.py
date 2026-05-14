from newspaper import Article

def get_news(url):

    try:
        article = Article(url)
        article.download()
        article.parse()



        return {
            "title": article.title or "untitled",
            "text":article.text.strip(),
            "date": str(article.publish_date) if article.publish_date else "unknown",
            "authors": article.authors or [],
            "url": url
            }
    except Exception as e:
        raise ValueError(f"Scraping Failed: {e}")

