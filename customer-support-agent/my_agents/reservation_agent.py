# 테이블 예약 처리하는 에이전트
from agents import Agent, RunContextWrapper

from guard.output_guardrail import validate_output_guardrail
from models import RestaurantContext
from tools import confirm_reservation


def dynamic_reservation_agent_instructions(
    wrapper: RunContextWrapper[RestaurantContext], agent: Agent[RestaurantContext]
):
    return f"""
    너는 {wrapper.context.name}의 테이블 예약을 도와주는데에 특화된 에이전트.

    예약에 필요한 정보:
    - 인원수
    - 희망 날짜
    - 희망 시간

    대화 기록에서 이미 제공된 정보는 다시 묻지 말고 부족한 정보만 질문해.
    위 정보를 모두 수집한 후 예약 내용을 복창하여 고객에게 확인을 받아.
    다른 Agent로 연결한다고 말하지 말고 예약 담당 역할에만 집중해.
    """


reservation_agent = Agent(
    name="Reservation_Agent",
    handoff_description="테이블 예약과 예약 인원수, 날짜 및 시간을 담당한다.",
    instructions=dynamic_reservation_agent_instructions,
    tools=[confirm_reservation],
    output_guardrails=[validate_output_guardrail],
)
