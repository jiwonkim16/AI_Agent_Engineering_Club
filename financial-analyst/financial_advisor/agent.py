# agent 생성 목적 파일
# agent.py 파일에는 필수적으로 root_agent 라는 변수가 있어야 함.
# 반드시 root_agent 여야 하는데, 이유는

from google.adk.agents import Agent

# Gemini 외에도 여러 LLM으로 작업할 수 있게 해주는 패키지
from google.adk.models.lite_llm import LiteLlm

MODEL = LiteLlm("openai/gpt-4o")


# tool (example)
def get_weather(city: str):
    return f"The weather in {city} is 30 degrees."


def convert_units(degrees: int):
    return "That is 40 farenheit"


geo_agent = Agent(
    name="GeoAgent",
    instruction="You help with geo questions",
    model=MODEL,
    description="Transfer to this agent when you have a geo related question.",
)

# Google ADK에서 Agent는 LlmAgent의 별칭
agent = Agent(
    name="WeatherAgent",
    instruction="You help the user with weather related questions.",
    model=MODEL,
    tools=[get_weather, convert_units],
    # OpenAI SDK의 Handoff와 같은 역할을 하는 것이 sub_agents
    sub_agents=[geo_agent],
)

root_agent = agent
