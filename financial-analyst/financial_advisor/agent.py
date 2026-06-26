# agent 생성 목적 파일
# agent.py 파일에는 필수적으로 root_agent 라는 변수가 있어야 함.

from cmd import PROMPT

from google.adk.agents import Agent

# Gemini 외에도 여러 LLM으로 작업할 수 있게 해주는 패키지
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import ToolContext

# agent를 tool로 변환
from google.adk.tools.agent_tool import AgentTool

# googel genai는 google AI API와 상호작용하는 python 클라이언트 라이브러리
from google.genai import types

from financial_advisor.sub_agents import data_analyst, financial_analyst, news_analyst

MODEL = LiteLlm("openai/gpt-4o")


# 원하는 tool이 context를 받도록 할 수 있음. 그리고 context로 state에 접근할 수 있음.
# from google.adk.tools import ToolContext
# summary 매개변수는 main Agent(financial advisor)의 요약본을 받기 위해서 임의로 추가, 이는 에이전트에서 자동으로 삽입해줌.
async def save_advice_report(tool_context: ToolContext, summary: str, ticker: str):
    state = tool_context.state
    data_analyst_result = state.get("data_analyst_result")
    financial_analyst_result = state.get("financial_analyst_result")
    news_analyst_analyst_result = state.get("news_analyst_analyst_result")
    report = f"""
        # Excetuve Summary and Advice:
        {summary}

        ## Data Analyst Report:
        {data_analyst_result}

        ## Financial Analyst Report:
        {financial_analyst_result}
        
        ## News Analyst Report:
        {news_analyst_analyst_result}
    """
    state["report"] = report

    # 파일명 지정
    filename = f"{ticker}_investment_advice.md"

    # Artifacts 생성
    # types는 미디어 컨텐츠 타입을 뜻함.
    artifact = types.Part(
        inline_data=types.Blob(
            mime_type="text/markdown",
            data=report.encode("utf-8"),
        )
    )

    await tool_context.save_artifact(filename, artifact)

    return {
        "success": True,
    }


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
