from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from youtube_shorts_maker.sub_agents.video_assembler.prompt import (
    VIDEO_ASSEMBLER_DESCRIPTION,
    VIDEO_ASSEMBLER_PROMPT,
)
from youtube_shorts_maker.sub_agents.video_assembler.tools import assemble_video

MODEL = LiteLlm(model="openai/gpt-4o")

video_assembler_agent = Agent(
    name="VideoAssemblerAgent",
    model=MODEL,
    description=VIDEO_ASSEMBLER_DESCRIPTION,
    instruction=VIDEO_ASSEMBLER_PROMPT,
    output_key="video_assembler_output",
    tools=[
        assemble_video,
    ],
)
