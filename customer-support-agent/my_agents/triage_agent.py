# 유저의 입력을 받고 올바른 에이전트에게 전달
# 주제와 관련된 질문인지를 확인하는 Guardrail 

import streamlit as st
from agents import (
    Agent,
    RunContextWrapper,
    input_guardrail,
    Runner,
    GuardrailFunctionOutput,
    handoff,
)
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from agents.extensions import handoff_filters
from models import UserAccountContext, InputGuardRailOutput, HandoffData
from my_agents.account_agent import account_agent
from my_agents.technical_agent import technical_agent
from my_agents.order_agent import order_agent
from my_agents.billing_agent import billing_agent

# Handoff(인계)
# handoff가 처리되는 방식에는 크게 2가지 옵션이 있는데,
# 1. handoff는 대화 자체가 다른 에이전트에게 넘어가야 함. (ex. A상담원과 대화 중 B 상담원으로 연결 전환, A 상담원과는 통신이 끊김)
# 2. 다른 에이전트를 tool로서 처리할 수 있음. (ex. A 상담원과 대화 중 A 상담원이 다른 상담원에게 내 질문과 관련된 정보를 얻어 A 상담원이 나에게 답변을 주는 형태)

# ---

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
    # RECOMMENDED_PROMPT_PREFIX는 OpenAI SDK에서 제공하는 프롬프트로, agent에 handoff가 있을 경우 agent 지침 최상단에 넣으라고 권장함.
    return f"""
    {RECOMMENDED_PROMPT_PREFIX}

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

# context는 어디든 따라가기 때문에 여기서도 context를 가져올 수 있음.
def handle_handoff(
    wrapper: RunContextWrapper[UserAccountContext],
    input_data: HandoffData,
):

    # handoff 가 발생하게된 이유 서술
    with st.sidebar:
        st.write(
            f"""
            Handing off to {input_data.to_agent_name}
            Reason: {input_data.reason}
            Issue Type: {input_data.issue_type}
            Description: {input_data.issue_description}
        """
        )


def make_handoff(agent):

    return handoff(
        agent=agent,
        on_handoff=handle_handoff,
        # AI 모델이 handoff를 호출 할때, HandoffData의 필드를 직접 채워서 tool 인자로 생성, 그 객체가 on_handoff 콜백의 input_data로 전달됨
        input_type=HandoffData,
        input_filter=handoff_filters.remove_all_tools, # 새로운 에이전트가 볼 데이터를 골라서 넘길 수 있게 해주는 필터. (extension에서 import)
        # 이 경우 에이전트가 호출했던 tool 사용 기록을 지워주고 유저와 에이전트 간 메세지만 남김.
    )



triage_agent = Agent(
    name="Triage_Agent",
     # instructions 시그니처를 보면 문자열을 넘길 수도 있고 RunContextWrapper와 에이전트를 매개변수로 받는 함수를 넘길 수도 있음.
     # 에이전트까지 호출하는 이유는 여러 에이전트에서 해당 함수가 사용될 수 있기 때문.
    instructions=dynamic_triage_agent_instructions,

    # input guardrail은 첫번째(진입) 에이전트에서만 실행됨. handoff로 넘어간 다른 에이전트에는 적용되지 않음.
    input_guardrails=[
        off_topic_guardrail
    ], # 이렇게 해두면 triage_agent가 실행되기 전에 off_topic_guardrail 함수가 먼저 실행됨.

    # 에이전트가 여러 개일 경우 일종의 tool로 사용 가능.
    # tools=[
    #     technical_agent.as_tool(
    #         tool_name="Technical Help Tool",
    #         tool_description="Use this when the user tech support"
    #     )
    # ]

    # handoff를 import 해서 handoff가 일어날 때 호출되는 함수 등등 여러가지를 할 수 있음.
    handoffs=[
        make_handoff(technical_agent),
        make_handoff(billing_agent),
        make_handoff(account_agent),
        make_handoff(order_agent),
    ]
)