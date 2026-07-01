from agents import Agent, RunContextWrapper

from models import BlogContext
from prompts import WRITING_INSTRUCTIONS


def writing_instructions(wrapper: RunContextWrapper[BlogContext], agent: Agent) -> str:
    ctx = wrapper.context
    extra = f"\n작성자 경험 메모: {ctx.experience}"
    if ctx.highlights:
        extra += f"\n강조하고 싶은 점: {ctx.highlights}"
    if ctx.rating is not None:
        if ctx.rating >= 4:
            extra += f"\n작성자 별점: {ctx.rating}점. 만족감을 강하게 드러내는 톤으로 써줘."
        else:
            extra += f"\n작성자 별점: {ctx.rating}점. 좋았던 점뿐 아니라 아쉬웠던 점도 솔직하게 언급해줘."
    return f"{WRITING_INSTRUCTIONS}\n\n{extra}"


writing_agent = Agent(
    name="WritingAgent",
    instructions=writing_instructions,
    model="gpt-5.4",
)
