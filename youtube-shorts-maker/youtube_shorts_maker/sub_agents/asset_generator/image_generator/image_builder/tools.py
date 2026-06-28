import base64

from google.adk.tools.tool_context import ToolContext
from google.genai import types
from openai import OpenAI

client = OpenAI()


# state에서 최적화된 각각의 프롬프트를 가져옴. 그걸로 이미지를 만들고 아티팩트에 저장.
async def generate_images(tool_context: ToolContext):

    prompt_builder_output = tool_context.state.get("prompt_builder_output")
    optimized_prompts = prompt_builder_output.get("optimized_prompts")

    # 에이전트가 툴을 여러번 호출하는 경우가 있는데 이럴 경우 이미 생성된 이미지는 다시 생성하고 싶지 않기 때문에 기존에 있는 아티팩트를 확인.
    existing_artifacts = await tool_context.list_artifacts()

    # tool의 출력 결과(생성된 이미지 정보)를 보여주고 싶어서 만듦.
    generated_images = []

    for prompt in optimized_prompts:
        scene_id = prompt.get("scene_id")
        enhanced_prompt = prompt.get("enhanced_prompt")
        filename = f"scene_{scene_id}_image.jpeg"

        if filename in existing_artifacts:
            generated_images.append(
                {
                    "scene_id": scene_id,
                    "prompt": enhanced_prompt[:100],
                    "filename": filename,
                }
            )
            continue
        # openAI을 활용하여 이미지 생성, base64로 인코딩되어 있는 상태.
        image = client.images.generate(
            model="gpt-image-1.5",  # 모델
            prompt=enhanced_prompt,
            n=1,  # 버전 갯수
            quality="low",
            moderation="low",  # 검열 수준
            output_format="jpeg",
            background="opaque",  # 불투명, transparent는 투명?
            size="1024x1536",
        )
        # 생성된 이미지는 base64로 인코딩 되어 있으므로 디코딩 필요.
        image_bytes = base64.b64decode(image.data[0].b64_json)

        # 디코딩된 byte로 아티팩트 생성
        artifact = types.Part(
            inline_data=types.Blob(
                mime_type="image/jpeg",
                data=image_bytes,
            )
        )

        await tool_context.save_artifact(
            filename=filename,
            artifact=artifact,
        )

        generated_images.append(
            {
                "scene_id": scene_id,
                "prompt": enhanced_prompt[:100],
                "filename": filename,
            }
        )

    return {
        "total_images": len(generated_images),
        "generated_images": generated_images,
        "status": "complete",
    }
