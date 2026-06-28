# GPT-Image-1 모델과 대화하는 이미지 제작 에이전트

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from youtube_shorts_maker.sub_agents.asset_generator.image_generator.image_builder.prompt import (
    IMAGE_BUILDER_DESCRIPTION,
    IMAGE_BUILDER_PROMPT,
)
from youtube_shorts_maker.sub_agents.asset_generator.image_generator.image_builder.tools import (
    generate_images,
)

MODEL = LiteLlm(model="openai/gpt-4o")

image_builder_agent = Agent(
    name="ImageBuilder",
    description=IMAGE_BUILDER_DESCRIPTION,
    instruction=IMAGE_BUILDER_PROMPT,
    model=MODEL,
    output_key="image_builder_output",
    tools=[
        generate_images,
    ],
)
