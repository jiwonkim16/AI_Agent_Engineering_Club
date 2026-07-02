from google.adk.agents import Agent, ParallelAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.tool_context import ToolContext
from google.genai import types

from story_book_maker.illustator.prompt import (
    ILLUSTRATOR_DESCRIPTION,
    ILLUSTRATOR_PROMPT,
)
from story_book_maker.illustator.tools import generate_images_for_page

MODEL = LiteLlm(model="openai/gpt-4o")


def before_image_generate(tool, args, tool_context: ToolContext):
    page_num = args["page_num"]
    tool_context.state["progress"] = f"🎇 이미지 {page_num}/5 생성 중..."
    return None


def after_image_generate(callback_context):
    page_num = int(callback_context.agent_name.split("_")[-1])
    return types.Content(
        role="model", parts=[types.Part(text=f"✅ 이미지 {page_num} 완료")]
    )


illustator_agent = [
    Agent(
        name=f"IllustatorAgent_page_{i}",
        instruction=ILLUSTRATOR_PROMPT.format(page_num=i),
        description=ILLUSTRATOR_DESCRIPTION,
        model=MODEL,
        tools=[generate_images_for_page],
        before_tool_callback=before_image_generate,
        after_agent_callback=after_image_generate,
    )
    for i in range(1, 6)
]

parallel_illustrator_agent = ParallelAgent(
    name="ParallelIllustatorAgent",
    sub_agents=illustator_agent,
)
