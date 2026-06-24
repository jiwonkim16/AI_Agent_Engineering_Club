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
