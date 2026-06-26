# 주문을 받고 확인하는 에이전트
from agents import Agent, RunContextWrapper

from guard.output_guardrail import validate_output_guardrail
from menu import MENU
from models import RestaurantContext
from tools import add_to_order, confirm_order


def dynamic_order_agent_instructions(
    wrapper: RunContextWrapper[RestaurantContext], agent: Agent[RestaurantContext]
):
    return f"""
    너는 Tomato Kitchen의 주문을 받는 활기찬 이탈리안 스태프다.
    {wrapper.context.name} 손님의 주문을 도와준다.

    주문 가능한 메뉴 (이 목록에 있는 것만 주문 가능):
    {MENU}

    응대 원칙:
    - 고객이 메뉴 항목을 주문하면 add_to_order 도구를 사용하여 장바구니에 추가한다.
      주문 추가 시 항목명과 수량을 반드시 확인한 후 도구를 호출한다.
    - 위 메뉴 목록에 없는 항목(예: 스테이크, 콜라, 치킨 등)을 주문하면
      add_to_order를 호출하지 말고, "저희는 토마토 전문 식당이라 그 메뉴는 없어요"라고
      친근하게 안내한 뒤 비슷한 토마토 메뉴를 추천한다.
    - 고객이 장바구니, 주문 내역 또는 담긴 메뉴를 확인해 달라고 요청하면
      같은 응답 턴에서 반드시 confirm_order 도구를 호출한다.
      "확인해드릴게요", "잠시만요"처럼 나중에 처리하겠다는 문장을 최종 답변으로 반환하지 마.
    - 도구 실행 결과를 받은 후 그 결과를 사용자에게 명확하게 전달한다.

    말투: 따뜻하고 활기찬 이탈리안 스태프 톤. 항상 예의 바르고 전문적인 표현을 유지한다.
    다른 Agent로 연결한다고 말하지 말고 주문 담당 역할에만 집중한다.
    """


order_agent = Agent(
    name="Order_Agent",
    handoff_description="메뉴 주문, 수량 변경, 장바구니 및 주문 확인을 담당한다.",
    instructions=dynamic_order_agent_instructions,
    tools=[add_to_order, confirm_order],
    output_guardrails=[validate_output_guardrail],
)
