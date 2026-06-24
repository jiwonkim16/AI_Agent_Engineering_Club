# agent 생성 목적 파일
# agent.py 파일에는 필수적으로 root_agent 라는 변수가 있어야 함.

from cmd import PROMPT

from google.adk.agents import Agent

# Gemini 외에도 여러 LLM으로 작업할 수 있게 해주는 패키지
from google.adk.models.lite_llm import LiteLlm

# agent를 tool로 변환
from google.adk.tools.agent_tool import AgentTool

from financial_advisor.sub_agents import data_analyst, financial_analyst, news_analyst

MODEL = LiteLlm("openai/gpt-4o")


def save_advice_report():
    pass


# Google ADK에서 Agent는 LlmAgent의 별칭
financial_advisor = Agent(
    name="FinancialAdvisor",
    instruction=PROMPT,
    model=MODEL,
    tools=[
        AgentTool(agent=financial_analyst),
        AgentTool(agent=news_analyst),
        AgentTool(agent=data_analyst),
        save_advice_report,
    ],
    # OpenAI SDK의 Handoff와 같은 역할을 하는 것이 sub_agents
    # sub_agents=[geo_agent],
)

root_agent = financial_advisor
