from google.adk.agents import Agent, LoopAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.tool_context import ToolContext

from .prompt import (
    CLARITY_EDITOR_DESCRIPTION,
    CLARITY_EDITOR_INSTRUCTION,
    EMAIL_OPTIMIZER_DESCRIPTION,
    EMAIL_SYNTHESIZER_DESCRIPTION,
    EMAIL_SYNTHESIZER_INSTRUCTION,
    LITERARY_CRITIC_DESCRIPTION,
    LITERARY_CRITIC_INSTRUCTION,
    PERSUASION_STRATEGIST_DESCRIPTION,
    PERSUASION_STRATEGIST_INSTRUCTION,
    TONE_STYLIST_DESCRIPTION,
    TONE_STYLIST_INSTRUCTION,
)

MODEL = LiteLlm(model="openai/gpt-4o-mini")

clarity_agent = Agent(
    name="ClarityEditorAgent",
    description=CLARITY_EDITOR_DESCRIPTION,
    instruction=CLARITY_EDITOR_INSTRUCTION,
    output_key="clarity_output",
    model=MODEL,
)

tone_stylist_agent = Agent(
    name="ToneStylistAgent",
    description=TONE_STYLIST_DESCRIPTION,
    instruction=TONE_STYLIST_INSTRUCTION,
    output_key="tone_output",
    model=MODEL,
)

persuation_agent = Agent(
    name="PersuationAgent",
    description=PERSUASION_STRATEGIST_DESCRIPTION,
    instruction=PERSUASION_STRATEGIST_INSTRUCTION,
    output_key="persuasion_output",
    model=MODEL,
)

email_synthesizer_agent = Agent(
    name="EmailSynthesizerAgent",
    description=EMAIL_SYNTHESIZER_DESCRIPTION,
    instruction=EMAIL_SYNTHESIZER_INSTRUCTION,
    output_key="synthesized_output",
    model=MODEL,
)


# 어떤 에이전트이던 간에 agent가 루프를 빠져나오게 만들 수 있음.
# 이를 위해 tool이 필요함.
# 어떤 tool이든 tool_context.actions.escalate(점진적으로 확대되다) 가 True 이면 Loop 종료.
# escalate라고 불리는 이유는 이게 더 상위 단계의 agent로 넘어갈 수 있기 때문.
# 예를 들어 분류 에이전트 하위의 에이전트들이 handoff 하기 위해 다시 상위(분류) 에이전트로 escalate 하는 tool을 사용함.
# 정리하면 LoopAgent 내부에서 escalate를 쓰면 Loop가 종료. 만약 상위의 분류 에이전트가 있고 하위 에이전트가 많이 있는 계층적인 구조에서
# escalate를 사용하면 하위 에이전트에서 escalate를 사용해서 대화의 주도권을 상위 에이전트로 보냄.
async def escalate_email_complete(tool_context: ToolContext):
    """Use this tool only when the email is good to go."""
    tool_context.actions.escalate = True
    return "Email optimization complete."


literary_critic_agent = Agent(
    name="LiteraryCriticAgent",
    description=LITERARY_CRITIC_DESCRIPTION,
    instruction=LITERARY_CRITIC_INSTRUCTION,
    tools=[
        escalate_email_complete,
    ],
    model=MODEL,
)

email_refiner_agent = LoopAgent(
    name="EmailRefinerAgent",
    # 50 이상 loop를 돌 수 없음.
    max_iterations=50,
    description=EMAIL_OPTIMIZER_DESCRIPTION,
    sub_agents=[
        clarity_agent,
        tone_stylist_agent,
        persuation_agent,
        email_synthesizer_agent,
        literary_critic_agent,
    ],
)

root_agent = email_refiner_agent
