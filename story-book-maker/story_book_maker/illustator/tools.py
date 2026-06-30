import base64

from google.adk.tools.tool_context import ToolContext
from google.genai import types
from openai import OpenAI

client = OpenAI()


async def generate_images(tool_context: ToolContext):
    story = tool_context.state.get("story_output")
    pages = story["pages"]

    existing_artifacts = await tool_context.list_artifacts()
    generated_images = []

    for page in pages:
        page_num = page["page"]
        visual = page["visual"]
        filename = f"page_{page_num}.png"

        if filename in existing_artifacts:
            generated_images.append({"page": page_num, "filename": filename})
            continue

        image = client.images.generate(
            model="gpt-image-1", prompt=visual, n=1, size="1024x1024"
        )

        image_bytes = base64.b64decode(image.data[0].b64_json)

        artifact = types.Part(
            inline_data=types.Blob(mime_type="image/png", data=image_bytes)
        )

        await tool_context.save_artifact(filename=filename, artifact=artifact)

        generated_images.append({"page": page_num, "filename": filename})

    return {"total_images": len(generated_images), "generated_images": generated_images}
