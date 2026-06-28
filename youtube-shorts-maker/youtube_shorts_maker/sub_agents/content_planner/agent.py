# 콘텐츠를 기획하는 에이전트 (사실상 영상 제작??)
from typing import List

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from pydantic import BaseModel, Field

from youtube_shorts_maker.sub_agents.content_planner.prompt import (
    CONTENT_PLANNER_DESCRIPTION,
    CONTENT_PLANNER_PROMPT,
)


# 프롬프트에 작성되어 있는 output format대로 모델을 구조화
# 모델의 각 필드에 대한 설명을 작성할 수 있음. -> pydantic Field.
class SceneOutput(BaseModel):
    id: int = Field(description="Scene ID number")
    narration: str = Field(description="Narration text for the scene")
    visual_description: str = Field(
        description="Detailed description for image generation"
    )
    embedded_text: str = Field(
        description="Text overlay for the image (can be any case/style)"
    )
    embedded_text_location: str = Field(
        description="Where to position the text on the image (e.g., 'top center', 'bottom left', 'middle right', 'center')"
    )
    duration: int = Field(description="Duration in seconds for this scene")


class ContentPlanOutput(BaseModel):
    topic: str = Field(description="The topic of the YouTube Short")
    total_duration: int = Field(description="Total video duration in seconds (max 20)")
    scenes: List[SceneOutput] = Field(
        description="List of scenes (agent decides how many)"
    )


MODEL = LiteLlm(model="openai/gpt-4o")

content_planner_agent = Agent(
    name="ContentPlannerAgent",
    description=CONTENT_PLANNER_DESCRIPTION,
    instruction=CONTENT_PLANNER_PROMPT,
    model=MODEL,
    # 출력 구조 설정.
    output_schema=ContentPlanOutput,
    # state에 저장. (주제, 영상 길이, 나레이션, 비주얼 설명 등등 정보를 다른 에이전트나 도구에서 접근할 수 있도록.)
    output_key="content_planner_output",
)
