import base64
import time

from google.adk.tools.tool_context import ToolContext
from google.genai import types
from openai import AsyncOpenAI

client = AsyncOpenAI()


async def generate_images_for_page(tool_context: ToolContext, page_num: int):
    story = tool_context.state.get("story_output")
    pages = story["pages"]
    character = story["character"]

    page = next(p for p in pages if p["page"] == page_num)
    visual = page["visual"]
    prompt = f"{character}. 이 장면: {visual}"
    filename = f"page_{page_num}.png"

    existing_artifacts = await tool_context.list_artifacts()
    if filename in existing_artifacts:
        return {"page": page_num, "filename": filename}

    print(f"[page] {page_num} 시작: {time.strftime('%H:%M:%S')}")
    image = await client.images.generate(
        model="gpt-image-1", prompt=prompt, n=1, size="1024x1024", quality="low"
    )
    print(f"[page] {page_num} 끝: {time.strftime('%H:%M:%S')}")

    image_bytes = base64.b64decode(image.data[0].b64_json)

    artifact = types.Part(
        inline_data=types.Blob(mime_type="image/png", data=image_bytes)
    )

    await tool_context.save_artifact(filename=filename, artifact=artifact)

    return {"page": page_num, "filename": filename}
