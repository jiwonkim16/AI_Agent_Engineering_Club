# 거대한 프롬프트 작성 대신 sequencial agent로 만듦.

from google.adk.agents import SequentialAgent

from youtube_shorts_maker.sub_agents.asset_generator.image_generator.image_builder.agent import (
    image_builder_agent,
)
from youtube_shorts_maker.sub_agents.asset_generator.image_generator.prompt_builder.agent import (
    prompt_builder_agent,
)

image_generator_agent = SequentialAgent(
    name="ImageGeneratorAgent",
    sub_agents=[prompt_builder_agent, image_builder_agent],
)
