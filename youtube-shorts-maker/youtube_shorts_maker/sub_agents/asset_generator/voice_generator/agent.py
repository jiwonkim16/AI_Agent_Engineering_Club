from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from youtube_shorts_maker.sub_agents.asset_generator.voice_generator.prompt import (
    VOICE_GENERATOR_DESCRIPTION,
    VOICE_GENERATOR_PROMPT,
)
from youtube_shorts_maker.sub_agents.asset_generator.voice_generator.tools import (
    generate_narrations,
)

MODEL = LiteLlm(model="openai/gpt-4o")

# 고품질 나레이션 음성을 생성하는 에이전트
# 프롬프트를 보면 state를 활용하고 있음.(content_planner_output)
# 음성 모델을 위한 프롬프트 생성 및 tools 호출 과 같은 2가지 역할을 수행 중.
voice_generator_agent = Agent(
    name="VoiceGeneratorAgent",
    description=VOICE_GENERATOR_DESCRIPTION,
    instruction=VOICE_GENERATOR_PROMPT,
    model=MODEL,
    tools=[
        generate_narrations,
    ],
)
