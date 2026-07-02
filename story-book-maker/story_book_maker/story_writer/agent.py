from typing import List

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.lite_llm import LiteLlm
from google.genai import types
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


def before_story_writing(callback_context: CallbackContext):
    print("📝 스토리 작성 중...")
    return None


def after_story_writing(callback_context: CallbackContext):
    return types.Content(role="model", parts=[types.Part(text="✅ 작성 완료")])


story_writer_agent = Agent(
    name="StoryWriterAgent",
    instruction=STORY_WRITER_PROMPT,
    description=STORY_WRITER_DESCRIPTION,
    model=MODEL,
    output_schema=StoryOutput,
    output_key="story_output",
    before_agent_callback=before_story_writing,
    after_agent_callback=after_story_writing,
)
