from agents import (
    Agent,
    GuardrailFunctionOutput,
    RunContextWrapper,
    Runner,
    input_guardrail,
)

from models import InputGuardRailOutput, RestaurantContext

input_guardrail_agent = Agent(
    name="Input_Guardrail_Agent",
    instructions="""
    사용자 요청이 식당 운영 범위 안의 요청인지 판단한다.

    다음은 모두 식당 범위 안의 정상 요청이므로 is_off_topic=False로 둔다:
    - 메뉴, 가격, 재료, 알레르기, 채식, 추천
    - 주문, 수량 변경, 장바구니, 주문 확인
    - 예약, 인원수, 날짜, 시간
    - 불만, 항의, 환불, 보상, 직원/음식/서비스에 대한 불쾌한 경험 호소, "사장/매니저 불러" 같은 격앙된 요구

    식당 운영과 전혀 무관한 주제(예: 일반 상식, 코딩 요청, 날씨, 정치 등)일 때만
    사유와 함께 is_off_topic=True로 trip-wire를 발동한다.
    표현이 거칠거나 화가 난 어조라도 식당 관련 불만이면 정상 요청으로 본다.
    """,
    output_type=InputGuardRailOutput,
)


@input_guardrail
async def off_topic_guardrail(
    wrapper: RunContextWrapper[RestaurantContext],
    agent: Agent[RestaurantContext],
    input: str,
):
    # 세션 사용 시 input에는 대화 히스토리(list)가 통째로 들어온다.
    # 과거 off-topic 발화가 현재 판정을 오염시키지 않도록 마지막 user 발화만 검사한다.
    if isinstance(input, list):
        user_messages = [m["content"] for m in input if m.get("role") == "user"]
        input = user_messages[-1] if user_messages else ""

    result = await Runner.run(input_guardrail_agent, input, context=wrapper.context)

    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=result.final_output.is_off_topic,
    )
