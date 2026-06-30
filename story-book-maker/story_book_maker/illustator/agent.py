from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from story_book_maker.illustator.prompt import (
    ILLUSTRATOR_DESCRIPTION,
    ILLUSTRATOR_PROMPT,
)
from story_book_maker.illustator.tools import generate_images

MODEL = LiteLlm(model="openai/gpt-4o")

illustator_agent = Agent(
    name="IllustatorAgent",
    instruction=ILLUSTRATOR_PROMPT,
    description=ILLUSTRATOR_DESCRIPTION,
    model=MODEL,
    tools=[generate_images],
)
