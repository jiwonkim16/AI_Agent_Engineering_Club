from agents import Agent, RunContextWrapper, WebSearchTool

from models import BlogContext
from prompts import RESEARCH_INSTRUCTIONS
from tools import naver_search


def research_instructions(wrapper: RunContextWrapper[BlogContext], agent: Agent) -> str:
    ctx = wrapper.context
    extra = f"\n강조하고 싶은 점: {ctx.highlights}" if ctx.highlights else ""
    return f"{RESEARCH_INSTRUCTIONS}{extra}"


research_agent = Agent(
    name="ResearchAgent",
    instructions=research_instructions,
    model="gpt-5.4-mini",
    tools=[WebSearchTool(), naver_search],
)
