from agents import Agent

from prompts import WRITING_INSTRUCTIONS

writing_agent = Agent(
    name="WritingAgent",
    instructions=WRITING_INSTRUCTIONS,
    model="gpt-5.4",
)
