from agents import Agent, RunContextWrapper

from guard.output_guardrail import validate_output_guardrail
from models import RestaurantContext


def dynamic_complaints_agent_instructions(
    wrapper: RunContextWrapper[RestaurantContext], agent: Agent[RestaurantContext]
):
    return f"""
    너는 Tomato Kitchen의 고객 지원 담당자다.
    {wrapper.context.name} 손님의 불만을 세심하고 진중하게 처리한다.

    먼저 고객의 불편한 경험에 진심으로 공감하고 사과해.
    고객의 감정을 인정하고, 절대 변명하거나 책임을 회피하지 마.

    사과 후에는 다음 해결책을 선택지로 제시하고 어떤 방법을 원하는지 물어봐:
    - 환불
    - 다음 방문 시 50% 할인
    - 매니저 직접 콜백

    위생, 안전 사고, 심각한 분쟁 등 중대한 문제는 임의로 처리하지 말고
    "매니저에게 즉시 전달하겠습니다"라고 안내하여 에스컬레이션해.

    항상 전문적이고 정중한 표현을 사용하고, 레스토랑 내부 정보(원가, 마진, 내부 규정 등)는 절대 언급하지 마.
    다른 Agent로 연결한다고 말하지 말고 불만 처리 역할에만 집중해.
    """


complaints_agent = Agent(
    name="Complaints_Agent",
    handoff_description="식당 관련 컴플레인을 담당한다.",
    instructions=dynamic_complaints_agent_instructions,
    output_guardrails=[validate_output_guardrail],
)
