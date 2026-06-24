# 주문을 받고 확인하는 에이전트
from agents import Agent, RunContextWrapper

from guard.output_guardrail import validate_output_guardrail
from models import RestaurantContext
from tools import add_to_order, confirm_order


def dynamic_order_agent_instructions(
    wrapper: RunContextWrapper[RestaurantContext], agent: Agent[RestaurantContext]
):
    return f"""
    너는 {wrapper.context.name}의 주문을 도와주는데에 특화된 에이전트.

    고객이 메뉴 항목을 주문하면 add_to_order 도구를 사용하여 장바구니에 추가해.
    주문 추가 시 항목명과 수량을 반드시 확인한 후 도구를 호출해.

    고객이 장바구니, 주문 내역 또는 담긴 메뉴를 확인해 달라고 요청하면
    같은 응답 턴에서 반드시 confirm_order 도구를 호출해.
    "확인해드릴게요", "잠시만요"처럼 나중에 처리하겠다는 문장을 최종 답변으로 반환하지 마.
    도구 실행 결과를 받은 후 그 결과를 사용자에게 명확하게 전달해.

    다른 Agent로 연결한다고 말하지 말고 주문 담당 역할에만 집중해.
    """


order_agent = Agent(
    name="Order_Agent",
    handoff_description="메뉴 주문, 수량 변경, 장바구니 및 주문 확인을 담당한다.",
    instructions=dynamic_order_agent_instructions,
    tools=[add_to_order, confirm_order],
    output_guardrails=[validate_output_guardrail],
)
