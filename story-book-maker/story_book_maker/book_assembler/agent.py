from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from story_book_maker.book_assembler.prompt import (
    BOOK_ASSEMBLER_DESCRIPTION,
    BOOK_ASSEMBLER_PROMPT,
)

MODEL = LiteLlm(model="openai/gpt-4o-mini")

book_assembler_agent = Agent(
    name="BookAssembler",
    description=BOOK_ASSEMBLER_DESCRIPTION,
    instruction=BOOK_ASSEMBLER_PROMPT,
    model=MODEL,
)
