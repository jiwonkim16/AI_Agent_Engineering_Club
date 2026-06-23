import streamlit as st
from agents import (
    Agent,
    GuardrailFunctionOutput,
    RunContextWrapper,
    Runner,
    handoff,
    input_guardrail,
)
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

from models import HandoffData, InputGuardRailOutput, RestaurantContext
from my_agents.menu_agent import menu_agent
from my_agents.order_agent import order_agent
from my_agents.reservation_agent import reservation_agent

input_guardrail_agent = Agent(
    name="Input_Guardrail_Agent",
    instructions="""
    사용자 요청이 레스토랑 예약, 주문, 메뉴 정보 관련 이슈임을 보장하고 이외 주제의 요청일 경우에는 사유와 함께 trip-wire 발동.
    """,
    output_type=InputGuardRailOutput,
)


@input_guardrail
async def off_topic_guardrail(
    wrapper: RunContextWrapper[RestaurantContext],
    agent: Agent[RestaurantContext],
    input: str,
):
    result = await Runner.run(input_guardrail_agent, input, context=wrapper.context)

    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=result.final_output.is_off_topic,
    )


def dynamic_triage_agent_instructions(
    wrapper: RunContextWrapper[RestaurantContext], agent: Agent[RestaurantContext]
):
    return f"""
    {RECOMMENDED_PROMPT_PREFIX}
    너는 레스토랑 요청을 분류하는 Triage Agent다.

    고객 정보:
    고객 이름: {wrapper.context.name},
    주문 정보: {wrapper.context.order},

    사용자의 가장 최근 요청과 대화 맥락을 확인하고 반드시 적절한 handoff 도구를 호출한다.

    - 메뉴, 가격, 재료, 채식, 알레르기, 추천 → Menu Agent
    - 주문 추가, 수량 변경, 장바구니, 주문 확인 → Order Agent
    - 예약, 인원수, 날짜, 시간 → Reservation Agent

    전문 영역에 해당하는 요청에 직접 답변하지 마라.
    전문가에게 연결한다고 텍스트로만 말하지 마라.
    안내 문구를 출력하지 말고 반드시 실제 transfer 도구를 호출하라.
    요청이 모호하여 담당 영역을 결정할 수 없는 경우에만 사용자에게 명확한 질문을 한다.
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
    ],
)
