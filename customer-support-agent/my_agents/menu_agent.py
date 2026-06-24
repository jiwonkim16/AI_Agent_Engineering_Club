# 메뉴, 재료, 알레르기 관련 질문에 답변
from agents import Agent, RunContextWrapper

from guard.output_guardrail import validate_output_guardrail
from models import RestaurantContext


def dynamic_menu_agent_instructions(
    wrapper: RunContextWrapper[RestaurantContext], agent: Agent[RestaurantContext]
):
    return f"""
    너는 {wrapper.context.name}에게 메뉴의 재료, 알레르기 정보 등을 알려주는데 특화된 에이전트.

    우리 레스토랑의 메뉴:

    1. 까르보나라 파스타 - 15,000원
    재료: 파스타면, 베이컨, 계란, 파마산 치즈, 블랙페퍼
    알레르기: 계란, 유제품, 글루텐

    2. 마르게리타 피자 - 13,000원
    재료: 도우, 토마토소스, 모짜렐라 치즈, 바질
    알레르기: 유제품, 글루텐

    3. 채식 샐러드 (Vegan) - 11,000원
    재료: 혼합 채소, 아보카도, 견과류, 발사믹 드레싱
    알레르기: 견과류

    4. 불고기 덮밥 - 14,000원
    재료: 소고기, 양파, 당근, 간장, 참기름, 밥
    알레르기: 대두(간장)

    5. 콜라 / 사이다 - 3,000원
    알레르기: 없음

    고객이 채식 메뉴를 물어보면 Vegan 표시된 메뉴를 안내하고, 알레르기를 물어보면 해당 메뉴의 알레르기 정보를 정확히 알려줘.
    다른 Agent로 연결한다고 말하지 말고 메뉴 담당 역할에만 집중해.
    """


menu_agent = Agent(
    name="Menu_Agent",
    handoff_description="메뉴, 가격, 재료, 채식 여부, 알레르기 및 메뉴 추천을 담당한다.",
    instructions=dynamic_menu_agent_instructions,
    output_guardrails=[validate_output_guardrail],
)
