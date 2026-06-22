# 출력 가드레일 (예시)

from agents import (
    Agent,
    output_guardrail,
    Runner,
    RunContextWrapper,
    GuardrailFunctionOutput,
)
from models import TechnicalOutputGuardRailOutput, UserAccountContext


technical_output_guardrail_agent = Agent(
    name="Technical Support Guardrail",
    instructions="""
    Analyze the technical support response to check if it inappropriately contains:
    
    - Billing information (payments, refunds, charges, subscriptions)
    - Order information (shipping, tracking, delivery, returns)
    - Account management info (passwords, email changes, account settings)
    
    Technical agents should ONLY provide technical troubleshooting, diagnostics, and product support.
    Return true for any field that contains inappropriate content for a technical support response.
    """,
    output_type=TechnicalOutputGuardRailOutput,
)


# output_guardrail 함수, 에이전트의 output_guardrails에 전달 (ex. output_guardrails=[technical_output_guardrail])
@output_guardrail
async def technical_output_guardrail(
    wrapper: RunContextWrapper[UserAccountContext],
    agent: Agent,
    # 에이전트가 낸 output
    output: str,
):
    # 에이전트의 output과 context를 받아 Runner 실행, 
    result = await Runner.run(
        technical_output_guardrail_agent,
        output,
        context=wrapper.context,
    )
    # output type을 지정해놓았으니 하나라도 true면 trip wire 발동.
    validation = result.final_output

    triggered = (
        validation.contains_off_topic
        or validation.contains_billing_data
        or validation.contains_account_data
    )

    # input guardrail과 마찬가지로 GuardrailFunctionOutput을 필수로 반환해야 함.
    return GuardrailFunctionOutput(
        output_info=validation,
        tripwire_triggered=triggered,
    )