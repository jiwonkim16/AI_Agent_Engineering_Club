from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.lite_llm import LiteLlm
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.tools.agent_tool import AgentTool
from google.genai import types

from youtube_shorts_maker.prompt import (
    SHORTS_PRODUCER_DESCRIPTION,
    SHORTS_PRODUCER_PROMPT,
)
from youtube_shorts_maker.sub_agents.asset_generator.agent import asset_generator_agent
from youtube_shorts_maker.sub_agents.content_planner.agent import content_planner_agent
from youtube_shorts_maker.sub_agents.video_assembler.agent import video_assembler_agent

MODEL = LiteLlm(model="openai/gpt-4o")


# Callback을 활용한 Guardrail 구현
# callback은 llm_request와 callback_context를 받음.
# callback_context에는 어느 에이전트에서 이 callback이 호출된건지, artifacts/state 조회, content의 내용 등등의 정보를 담고 있음.
def before_model_callback(
    callback_context: CallbackContext,
    llm_request: LlmRequest,
):
    # print(callback_context.agent_name)
    history = llm_request.contents
    last_message = history[-1]
    if last_message.role == "user":
        text = last_message.parts[0].text
        if "hummus" in text:
            return LlmResponse(
                content=types.Content(
                    parts=[
                        types.Part(text="Sorry I can't help with that."),
                    ],
                    role="model",
                )
            )
    return None  # callback이 None을 return 하는건, 그냥 정상동작하라는 의미.


shorts_producer_agent = Agent(
    name="ShortsProducerAgent",
    instruction=SHORTS_PRODUCER_PROMPT,
    # 이 에이전트가 무엇을 하며 뭘해야 하는지에 대한 설명.
    description=SHORTS_PRODUCER_DESCRIPTION,
    model=MODEL,
    # 콘텐츠 플래너로 기획 → 에셋 제너레이터로 이미지 생성까지 도구로 연결
    tools=[
        AgentTool(agent=content_planner_agent),
        AgentTool(agent=asset_generator_agent),
        AgentTool(agent=video_assembler_agent),
    ],
    # callback 설정
    before_model_callback=before_model_callback,
)

root_agent = shorts_producer_agent
