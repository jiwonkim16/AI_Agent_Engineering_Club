from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from tools import web_search_tool

MODEL = LiteLlm(model="openai/gpt-4o")

# firecrwal 대신 yfinance의 get_news API를 사용해도 됨. 이 방법이 비용을 절약할 수 있는 더 좋은 방법임. 공식문서 참고.
news_analyst = Agent(
    name="NewsAnalyst",
    model=MODEL,
    # root_agent가 볼 수 있도록, 이 에이전트가 언제 필요한지 판단할 수 있도록 역할/기준을 기술
    description="Uses Web Search tools to search and scrape real web content from the web.",
    instruction="""
    You are a News Analyst Specialist who uses web tools to find current information. Your job:
    
    1. **Web Search**: Use web_search_tool() to find recent news about a company.
    3. **Summarize Findings**: Explain what you found and its relevance
    
    **Your Web Tools:**
    - **web_search_tool()**: Firecrawl web search for company news
    
    Use external APIs to search and scrape web content for current information.
    """,
    tools=[
        web_search_tool,
    ],
    # agent가 state에 데이터를 저장하는 방법
    output_key="news_analyst_result",
)
