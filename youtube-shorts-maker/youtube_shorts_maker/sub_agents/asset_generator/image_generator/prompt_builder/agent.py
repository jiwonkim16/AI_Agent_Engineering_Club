# 프롬프트 생성 에이전트
# 콘텐츠 기획에서 visual description을 가져오고 그 프롬프트를 gpt-image-1 model에 맞게 최적화하는 역할.
# 대부분의 경우 프롬프트만 작성해서 출력 구조를 설정할 수도 있지만 좀더 확실하게 하기 위해서 아래와 같이 pydantic 모델로 만들고 output_schema를 적용해줄 수 있음.
from typing import List

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from pydantic import BaseModel, Field

from youtube_shorts_maker.sub_agents.asset_generator.image_generator.prompt_builder.prompt import (
    PROMPT_BUILDER_DESCRIPTION,
    PROMPT_BUILDER_PROMPT,
)

MODEL = LiteLlm(model="openai/gpt-4o")


class OptimizedPrompt(BaseModel):
    scene_id: int = Field(description="Scene ID from the original content plan")
    enhanced_prompt: str = Field(
        description="Detailed prompt with technical specs and text overlay instructions for vertical YouTube Shorts"
    )


class PromptBuilderOutput(BaseModel):
    optimized_prompts: List[OptimizedPrompt] = Field(
        description="Array of optimized image generation prompts for vertical YouTube Shorts"
    )


prompt_builder_agent = Agent(
    name="PromptBuilderAgent",
    description=PROMPT_BUILDER_DESCRIPTION,
    instruction=PROMPT_BUILDER_PROMPT,
    model=MODEL,
    output_schema=PromptBuilderOutput,
    output_key="prompt_builder_output",
)
