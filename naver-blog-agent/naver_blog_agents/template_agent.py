from agents import Agent, RunContextWrapper

from models import BlogContext
from prompts import TEMPLATE_INSTRUCTIONS


def template_instructions(wrapper: RunContextWrapper[BlogContext], agent: Agent) -> str:
    ctx = wrapper.context
    extra = f"\n작성자 경험 메모: {ctx.experience}"
    if ctx.highlights:
        extra += f"\n강조하고 싶은 점: {ctx.highlights} (이 내용이 들어갈 섹션을 명시해줘)"
    return f"{TEMPLATE_INSTRUCTIONS}\n\n{extra}"


template_agent = Agent(
    name="TemplateAgent",
    instructions=template_instructions,
    model="gpt-5.4-mini",
)
