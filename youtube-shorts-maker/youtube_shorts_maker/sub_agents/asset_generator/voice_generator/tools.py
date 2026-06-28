from typing import Any, Dict, List

from google.adk.tools.tool_context import ToolContext
from google.genai import types
from openai import OpenAI

client = OpenAI()


# image_builder tool과 거의 동일한 방식으로 tool 생성함.
# 먼저, 모델이 state에 있는 값을 가지고 옴. 그리고 각 장면을 어떻게 나레이션할지 알려줌.


# 그리고나서 generate_narrations tool을 실행하면
# 이미 만들어진 audio file들의 artifact를 불러옴.(동일한 오디오 파일을 재생성하지 않기 위해)
# OpenAI의 text-to-speech-model(텍스트 음성 변환 모델)을 호출해서 디코딩하고 artifact를 생성.
async def generate_narrations(
    tool_context: ToolContext, voice: str, voice_instructions: List[Dict[str, Any]]
):
    """
    Generate narration audio for each scene using OpenAI TTS API

    Args:
        tool_context: Tool context to access artifacts and save files
        voice: Selected voice for TTS (alloy, echo, fable, onyx, nova, shimmer)
        voice_instructions: List of dictionaries containing narration instructions for each scene

    Returns:
        Information about all generated audio files
    """

    existing_artifacts = await tool_context.list_artifacts()

    generated_narrations = []

    for instruction in voice_instructions:
        text_input = instruction.get("input")
        instructions = instruction.get("instructions")
        scene_id = instruction.get("scene_id")
        filename = f"scene_{scene_id}_narration.mp3"

        if filename in existing_artifacts:
            generated_narrations.append(
                {
                    "scene_id": scene_id,
                    "filename": filename,
                    "input": text_input,
                    "instructions": instructions[:50],
                }
            )
            continue
        # 오디오 파일 생성 방법 : with client.audio.speech
        # 모델과 목소리를 선택,모델이 말할 내용을 입력한 다음, instruction으로 지침을 내려준 다음
        # 파일에 pipe 하면 됨. (pipe 하면 된다는게 무슨 의미인지??)
        with client.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts",
            voice=voice,
            input=text_input,
            instructions=instructions,
        ) as response:
            audio_data = response.read()

        # audio_data 와 같은 byte 파일로 아티팩트 생성
        artifact = types.Part(
            inline_data=types.Blob(mime_type="audio/mpeg", data=audio_data)
        )

        await tool_context.save_artifact(
            filename=filename,
            artifact=artifact,
        )
        generated_narrations.append(
            {
                "scene_id": scene_id,
                "filename": filename,
                "input": text_input,
                "instructions": instructions[:50],
            }
        )

    return {
        "success": True,
        "narrations": generated_narrations,
        "total_narrations": len(generated_narrations),
    }
