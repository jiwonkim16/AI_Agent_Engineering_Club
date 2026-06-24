from agents import (
    Agent,
    GuardrailFunctionOutput,
    RunContextWrapper,
    Runner,
    output_guardrail,
)

from models import OutputGuardRailOutput, RestaurantContext

output_guardrail_agent = Agent(
    name="Output_Guardrail_Agent",
    instructions="""
    에이전트가 고객에게 보낼 응답을 검사한다. 다음 두 가지를 판단한다.

    1. reveals_internal_info: 레스토랑 내부 정보(원가, 마진, 매입가, 내부 규정·매뉴얼, 직원 개인정보 등)를 노출하면 True.
    2. is_unprofessional: 무례하거나 비전문적이거나 정중하지 않은 표현이 있으면 True.

    둘 중 하나라도 True이면 사유를 reason에 담는다.
    정상적인 메뉴 안내, 주문 처리, 예약 확인, 불만 응대(사과·공감·해결책 제시)는 두 항목 모두 False로 둔다.
    """,
    output_type=OutputGuardRailOutput,
)


@output_guardrail
async def validate_output_guardrail(
    wrapper: RunContextWrapper[RestaurantContext],
    agent: Agent[RestaurantContext],
    output: str,
):
    result = await Runner.run(output_guardrail_agent, output, context=wrapper.context)

    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=result.final_output.reveals_internal_info
        or result.final_output.is_unprofessional,
    )
