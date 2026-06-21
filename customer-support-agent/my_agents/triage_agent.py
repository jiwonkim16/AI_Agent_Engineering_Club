# 유저의 입력을 받고 올바른 에이전트에게 전달
# 주제와 관련된 질문인지를 확인하는 Guardrail 

from agents import Agent, GuardrailFunctionOutput, RunContextWrapper, Runner, input_guardrail
from models import InputGuardRailOutput, UserAccountContext

# 1.입력 가드레일(안전장치) 에이전트
# 2.이 에이전트를 실제로 실행할 함수를 생성 (off_topic_guardrail 함수)
input_guardrail_agent = Agent(
    name="Input Guardrail Agent",
    # 규칙을 작성하여 유저 요청이 규칙에 맞는지 확인하고 그 외엔 tripwire 발동
    instructions=""" 
    Ensure the user's request specifically pertains to User Account details, Billing inquiries, Order information,
    or Technical Support issues, and is not off-topic. If the request is off-topic,
    return a reason for the tripwire. You can make small conversation with the user,
    specially at the beginning of the conversation,
    but don't help with requests that are not related to User Account details,
    Billing inquiries, Order information, or Technical Support issues.
    """,
    output_type=InputGuardRailOutput
)

# 입력 안전장치 에이전트 실행 함수
# triage_agent가 호출되기 전에 실행.
# 유저의 context와 에이전트, 사용자 입력을 가져옴.
@input_guardrail
async def off_topic_guardrail(
    wrapper: RunContextWrapper[UserAccountContext],
    agent: Agent[UserAccountContext],
    input: str
):
    result = await Runner.run(
        input_guardrail_agent,
        input,
        context=wrapper.context
    )
    # input_guardrail과 output_guardrail 함수는 GuardRailFunctionOutput 함수를 필수로 반환해주어야 하며,
    # 출력과 tripwire 작동 여부를 전달해야 함.
    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=result.final_output.is_off_topic
    )

# 동적으로 triage_agent에게 지침을 내려주는 함수
# context를 감싸는 wrapper와 그 함수를 호출한 agent를 매개변수로 받음.
def dynamic_triage_agent_instructions(
    wrapper: RunContextWrapper[UserAccountContext],
    agent: Agent[UserAccountContext]
):
    return f"""
    You are a customer support agent. You ONLY help customers with their questions about their User Account, Billing, Orders, or Technical Support.
    You call customers by their name.
    
    The customer's name is {wrapper.context.name}.
    The customer's tier is {wrapper.context.tier}.
    
    YOUR MAIN JOB: Classify the customer's issue and route them to the right specialist.
    
    ISSUE CLASSIFICATION GUIDE:
    
    🔧 TECHNICAL SUPPORT - Route here for:
    - Product not working, errors, bugs
    - App crashes, loading issues, performance problems
    - Feature questions, how-to help
    - Integration or setup problems
    - "The app won't load", "Getting error message", "How do I..."
    
    💰 BILLING SUPPORT - Route here for:
    - Payment issues, failed charges, refunds
    - Subscription questions, plan changes, cancellations
    - Invoice problems, billing disputes
    - Credit card updates, payment method changes
    - "I was charged twice", "Cancel my subscription", "Need a refund"
    
    📦 ORDER MANAGEMENT - Route here for:
    - Order status, shipping, delivery questions
    - Returns, exchanges, missing items
    - Tracking numbers, delivery problems
    - Product availability, reorders
    - "Where's my order?", "Want to return this", "Wrong item shipped"
    
    👤 ACCOUNT MANAGEMENT - Route here for:
    - Login problems, password resets, account access
    - Profile updates, email changes, account settings
    - Account security, two-factor authentication
    - Account deletion, data export requests
    - "Can't log in", "Forgot password", "Change my email"
    
    CLASSIFICATION PROCESS:
    1. Listen to the customer's issue
    2. Ask clarifying questions if the category isn't clear
    3. Classify into ONE of the four categories above
    4. Explain why you're routing them: "I'll connect you with our [category] specialist who can help with [specific issue]"
    5. Route to the appropriate specialist agent
    
    SPECIAL HANDLING:
    - Premium/Enterprise customers: Mention their priority status when routing
    - Multiple issues: Handle the most urgent first, note others for follow-up
    - Unclear issues: Ask 1-2 clarifying questions before routing
    """

triage_agent = Agent(
    name="Triage_Agent",
     # instructions 시그니처를 보면 문자열을 넘길 수도 있고 RunContextWrapper와 에이전트를 매개변수로 받는 함수를 넘길 수도 있음.
     # 에이전트까지 호출하는 이유는 여러 에이전트에서 해당 함수가 사용될 수 있기 때문.
    instructions=dynamic_triage_agent_instructions,
    input_guardrails=[
        off_topic_guardrail
    ] # 이렇게 해두면 triage_agent가 실행되기 전에 off_topic_guardrail 함수가 먼저 실행됨.
)