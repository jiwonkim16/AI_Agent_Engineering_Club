import streamlit as st
from agents import (
    Agent,
    RunContextWrapper,
    handoff,
)
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

from guard.input_guardrail import off_topic_guardrail
from models import HandoffData, RestaurantContext
from my_agents.complaints_agent import complaints_agent
from my_agents.menu_agent import menu_agent
from my_agents.order_agent import order_agent
from my_agents.reservation_agent import reservation_agent


def dynamic_triage_agent_instructions(
    wrapper: RunContextWrapper[RestaurantContext], agent: Agent[RestaurantContext]
):
    return f"""
    {RECOMMENDED_PROMPT_PREFIX}
    너는 토마토 전문 식당 Tomato Kitchen의 입구에서 손님을 맞이하는 호스트다.
    손님의 요청을 알맞은 담당자에게 연결한다.

    고객 정보:
    고객 이름: {wrapper.context.name},
    주문 정보: {wrapper.context.order},

    사용자의 가장 최근 요청과 대화 맥락을 확인하고 반드시 적절한 handoff 도구를 호출한다.

    - 메뉴, 가격, 재료, 채식, 알레르기, 추천 → Menu Agent
    - 주문 추가, 수량 변경, 장바구니, 주문 확인 → Order Agent
    - 예약, 인원수, 날짜, 시간 → Reservation Agent
    - 음식/서비스/직원에 대한 불만, 항의, 환불 요청, 불쾌한 경험 호소 → Complaints Agent

    전문 영역에 해당하는 요청에 직접 답변하지 마라.
    전문가에게 연결한다고 텍스트로만 말하지 마라.
    안내 문구를 출력하지 말고 반드시 실제 transfer 도구를 호출하라.
    요청이 모호하여 담당 영역을 결정할 수 없는 경우에만 손님에게 친근하고 따뜻하게 되묻는다.
    """


def make_handoff(agent):
    def handle_handoff(
        wrapper: RunContextWrapper[RestaurantContext], input_data: HandoffData
    ):
        logs = st.session_state.setdefault("handoff_logs", [])
        logs.append(
            {
                "to_agent": agent.name,
                "reason": input_data.reason,
                "summary": input_data.summary,
            }
        )

    return handoff(agent=agent, on_handoff=handle_handoff, input_type=HandoffData)


triage_agent = Agent(
    name="Triage_Agent",
    instructions=dynamic_triage_agent_instructions,
    input_guardrails=[off_topic_guardrail],
    handoffs=[
        make_handoff(menu_agent),
        make_handoff(order_agent),
        make_handoff(reservation_agent),
        make_handoff(complaints_agent),
    ],
)
