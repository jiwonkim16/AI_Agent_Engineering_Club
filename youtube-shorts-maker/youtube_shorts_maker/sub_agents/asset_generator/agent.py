# 병렬 에이전트 워크플로우
# image_generator_agent는 순차(sequencial) 에이전트(workflow, 내부 각 서브에이전트가 LlmAgent이지 image_generator_agent 자체는 일종의 함수.) 이지만
# voice_generator_agent와 병렬로 실행됨.
from google.adk.agents import ParallelAgent

from youtube_shorts_maker.sub_agents.asset_generator.prompt import (
    ASSET_GENERATOR_DESCRIPTION,
)
from youtube_shorts_maker.sub_agents.asset_generator.voice_generator.agent import (
    voice_generator_agent,
)

from .image_generator.agent import image_generator_agent

asset_generator_agent = ParallelAgent(
    name="AssetGeneratorAgent",
    description=ASSET_GENERATOR_DESCRIPTION,
    sub_agents=[image_generator_agent, voice_generator_agent],
)
