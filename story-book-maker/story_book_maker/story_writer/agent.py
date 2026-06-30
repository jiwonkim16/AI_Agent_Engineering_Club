from typing import List

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from pydantic import BaseModel

from story_book_maker.story_writer.prompt import (
    STORY_WRITER_DESCRIPTION,
    STORY_WRITER_PROMPT,
)

MODEL = LiteLlm(model="openai/gpt-4o")


class PageOutput(BaseModel):
    page: int
    text: str
    visual: str


class StoryOutput(BaseModel):
    theme: str
    character: str
    pages: List[PageOutput]


story_writer_agent = Agent(
    name="StoryWriterAgent",
    instruction=STORY_WRITER_PROMPT,
    description=STORY_WRITER_DESCRIPTION,
    model=MODEL,
    output_schema=StoryOutput,
    output_key="story_output",
)
