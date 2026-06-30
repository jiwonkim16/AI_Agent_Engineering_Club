from agents import Agent, WebSearchTool

from prompts import RESEARCH_INSTRUCTIONS
from tools import naver_search

research_agent = Agent(
    name="ResearchAgent",
    instructions=RESEARCH_INSTRUCTIONS,
    model="gpt-5.4-mini",
    tools=[WebSearchTool(), naver_search],
)
