import asyncio
from pydantic import BaseModel, Field
from restack_ai.workflow import workflow, import_functions, log
from datetime import timedelta

# ✅ Import functions correctly
with import_functions():
    from src.functions.llm import llm, FunctionInputParams
    from src.functions.news import fetch_news  # ✅ Correct import

class WorkflowInputParams(BaseModel):
    size: int = Field(default=5, ge=1, le=50, description="Number of articles to fetch (1-50)")

@workflow.defn()
class NewsWorkflow:
    @workflow.run
    async def run(self, input: WorkflowInputParams):
        log.info("NewsWorkflow started", input=input)

        # Step 1: Fetch news articles
        news_data = await workflow.step(
            fetch_news,
             input.size,
            start_to_close_timeout=timedelta(seconds=120)
        )

        log.info("Fetched news data", news_data=news_data)  # ✅ Debug log

        # Ensure news_data is not empty
        if not news_data:
            log.error("No news articles found, skipping summarization.")
            return {"news": []}

        # Step 2: Prepare LLM input for parallel execution
        async def summarize_article(article):
            try:
                # ✅ Use description or title if content is missing
                article_text = article.get("content", "").strip()
                if not article_text or "ONLY AVAILABLE" in article_text:
                    article_text = article.get("description",  "No summary available")

                log.info("Processing article", title=article["title"])

                llm_summary = await workflow.step(
                    llm,
                    FunctionInputParams(
                        system_content="You are a helpful AI assistant that summarizes news articles concisely.",
                        user_content=f"Summarize this article in 2 sentences:\n\n{article_text}",
                        model="gpt-4o-mini"
                    ),
                    start_to_close_timeout=timedelta(seconds=60)
                )

                log.info("Generated summary", title=article["title"], summary=llm_summary)

                return {
                    "image_url": article["image_url"],
                    "title": article["title"],
                    "summary": llm_summary
                }
            except Exception as e:
                log.error(f"Error summarizing article: {e}")
                return None  # If error, return None so we can filter it out

        # Step 3: Run all LLM steps in parallel
        summaries = await asyncio.gather(*[summarize_article(article) for article in news_data])

        # Remove None values (failed articles)
        summarized_news = [s for s in summaries if s is not None]

        log.info("NewsWorkflow completed", summarized_news=summarized_news)
        return {"news": summarized_news}
