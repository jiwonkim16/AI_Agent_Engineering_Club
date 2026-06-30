from agents import Agent

from prompts import TEMPLATE_INSTRUCTIONS

template_agent = Agent(
    name="TemplateAgent",
    instructions=TEMPLATE_INSTRUCTIONS,
    model="gpt-5.4-mini",
)
