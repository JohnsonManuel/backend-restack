from restack_ai.function import function, log
import aiohttp

@function.defn()
async def fetch_news(size: int = 3) -> list:
    """
    Fetches the latest news articles from NewsData.io API.
    
    Args:
        size (int): Number of articles to fetch (1-50).
    
    Returns:
        list: A list of news articles containing "image_url", "title", and "content".
    """
    api_key = "pub_68448f80078b7d556e75ab0338d0e4c7170ff"  # Replace with your actual API key
    url = f"https://newsdata.io/api/1/latest?apikey={api_key}&size={size}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                log.info("Response from News API", status=response.status)
                
                if response.status == 200:
                    data = await response.json()
                    log.info("Fetched news data", data=data)
                    
                    articles = data.get("results", [])
                    
                    # Extract only relevant fields
                    news_articles = [
                        {
                            "image_url": article.get("image_url", ""),
                            "title": article.get("title", ""),
                            "description": article.get("description", "")  # Full content for LLM summarization
                        }
                        for article in articles
                    ]
                    
                    return news_articles
                
                else:
                    log.error(f"News API request failed with status: {response.status}")
                    raise Exception(f"Error: {response.status}")

    except Exception as e:
        log.error(f"Exception occurred while fetching news: {e}")
        raise e
