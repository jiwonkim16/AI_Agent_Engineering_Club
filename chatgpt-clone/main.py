from agents.run import CallModelData, ModelInputData
import dotenv

dotenv.load_dotenv()
from openai import OpenAI
import asyncio
import base64
import streamlit as st
from agents import Agent, Runner, SQLiteSession, WebSearchTool, FileSearchTool, ImageGenerationTool, RunConfig

client = OpenAI()

VECTOR_STORE_ID = "vs_6a2ffc988cdc8191a8016140e04df2cb"

if "agent" not in st.session_state:
    st.session_state["agent"] = Agent(
        name="Life Coach Agent",
        instructions="""
            너는 Life Coach Assistant야.
            사용자의 목표 달성, 자기계발, 습관 형성, 동기부여를 돕는 따뜻하고
            긍정적인 코치야. 사용자를 격려하되, 조언은 막연한 응원이 아니라
            구체적이고 실행 가능한 내용이어야 해.

            아래 도구들을 상황에 맞게 능동적으로 활용해서 답변해:

            - Web Search Tool : 최신 정보, 검증된 팁, 동기부여 콘텐츠, 자기계발
                방법 등 외부 지식이 필요할 때 검색해서 근거 있는 조언을 제공해.

            - File Search Tool : 사용자 개인에 관한 질문(목표, 계획, 일기, 진행
                상황 등)에 답할 때, 저장된 사용자의 파일을 먼저 조회해서 실제 내용을
                바탕으로 답변해. 추측하지 말고 파일에 있는 사실을 활용해.

            - Image Generation Tool : 사용자의 목표, 성취, 꿈, 진행 상황을 시각적으로
                표현하면 동기부여에 도움이 될 때 이미지를 생성해
                (예: 목표 달성 축하 이미지, 비전 보드, 진행 상황 시각화).
                단, 사용자 개인의 목표나 계획을 시각화할 때는 반드시 먼저 File Search
                Tool로 실제 목표를 조회하고, 그 구체적인 내용을 이미지에 반영해.
                막연한 이미지가 아니라 사용자의 실제 목표가 담긴 이미지를 만들어야 해.

            여러 도구를 함께 사용해야 할 때는 자연스럽게 연결해서 사용해.
            예를 들어 비전 보드를 만들 때는 먼저 사용자의 목표를 조회한 뒤,
            그 목표들을 시각 요소로 담아 이미지를 생성해.
        """,
        tools=[
            WebSearchTool(),
            FileSearchTool(
                vector_store_ids=[VECTOR_STORE_ID],
                max_num_results=3
            ),
            ImageGenerationTool(
                tool_config={
                    "type": "image_generation",
                    "quality": "medium",
                    "output_format": "png",
                    "moderation": "low",
                    "partial_images": 1
                }
            )
        ]
    )

agent = st.session_state["agent"]

if "session" not in st.session_state:
    st.session_state["session"] = SQLiteSession("chat-history", "life-coach-memory.db")

session = st.session_state["session"]

if "goals" not in st.session_state:
    st.title("🎯 목표를 알려주세요.")
    st.write("코치가 당신을 도울 수 있도록 올해 목표를 입력해주세요.")
    st.caption("형식 : 각 목표는 '-'로 시작, 달성한 목표엔 ✅ 추가")

    goals_text = st.text_area("나의 목표", height=300, placeholder="## 운동\n- 주 3회 운동 \n- 책 10권 읽기 ✅")

    if st.button("시작하기"):
        if not goals_text.strip():
            st.warning("목표를 입력해주세요.")
        else:
            # session_state에 저장
            st.session_state["goals"] = goals_text
            # vector store에 업로드
            uploaded_file = client.files.create(
                file=("my_goals.txt", goals_text.encode("utf-8")),
                purpose="user_data"
            )
            client.vector_stores.files.create(
                vector_store_id=VECTOR_STORE_ID,
                file_id=uploaded_file.id
            )
            # st.rerun()
            st.rerun()

    st.stop()

async def paint_history():
    messages = await session.get_items()

    for message in messages:
        if "role" in message:
            with st.chat_message(message["role"]):
                if message["role"] == "user":
                    content = message["content"]
                    if isinstance(content, str):
                        st.write(content)
                    elif isinstance(content, list):
                        for part in content:
                            if "image_url" in part:
                                st.image(part["image_url"])
                else:
                    if message["type"] == "message":
                        st.write(message["content"][0]["text"])
        if "type" in message:
            message_type = message["type"]
            if message_type == "web_search_call":
                with st.chat_message("ai"):
                    st.write("🚀 웹 검색 ...")
            elif message_type == "file_search_call":
                with st.chat_message("ai"):
                    st.write("📂 파일 검색 ...")
            elif message_type == "image_generation_call":
                result = message.get("result")
                if result:
                    image = base64.b64decode(result)
                    with st.chat_message("ai"):
                        st.image(image)

asyncio.run(paint_history())

def calc_progress(text):
    lines = text.split("\n")
    total = 0
    done = 0
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("- "):
            total += 1
            if "✅" in stripped:
                done += 1
    return done, total

def update_status(status_container, event):
    status_messages = {
        'response.web_search_call.completed': ("✅ 웹 검색 완료", "complete"),
        'response.web_search_call.in_progress': ("🤖 웹 검색 시작...", "running"),
        'response.web_search_call.searching': ("⏳ 웹 검색 중... ", "running"),
        'response.file_search_call.completed': ("✅ 파일 검색 완료", "complete"),
        'response.file_search_call.in_progress': ("📃 파일 검색 시작...", "running"),
        'response.file_search_call.searching': ("⏳ 파일 검색 중... ", "running"),
        'response.image_generation_call.generating': ("🎨 이미지 생성 중...", "running"),
        'response.image_generation_call.in_progress': ("🎨 이미지 생성 중...", "running"),
        'response.image_generation_call.completed': ("✅ 이미지 생성 완료", "complete"),
        'response.completed': (" ", "complete")
    }

    if event in status_messages:
        label, state = status_messages[event]
        status_container.update(label=label, state=state)

TOOL_CALL_TYPES = {"web_search_call", "file_search_call", "image_generation_call"}

def filter_tool_calls(data: CallModelData) -> ModelInputData:
    def item_type(item):
        if isinstance(item, dict):
            return item.get("type")
        return getattr(item, "type", None)

    cleaned = [item for item in data.model_data.input if item_type(item) not in TOOL_CALL_TYPES]
    return ModelInputData(input=cleaned, instructions=data.model_data.instructions)


async def run_agent(message):
    with st.chat_message("ai"):
        status_container = st.status("🌿", expanded=False)
        image_placeholder = st.empty()
        text_placeholder = st.empty()
        response = ""

        st.session_state["image_placeholder"] = image_placeholder
        st.session_state["text_placeholder"] = text_placeholder

        stream = Runner.run_streamed(
            agent,
            message,
            session=session,
            run_config=RunConfig(call_model_input_filter=filter_tool_calls)
        )

        async for event in stream.stream_events():
            if event.type == "run_item_stream_event":
                if event.name == "tool_called":
                    raw_item = event.item.raw_item
                    if getattr(raw_item, "type", None) == "web_search_call":
                        query = raw_item.action.query
                        status_container.update(label=f"🔍 웹 검색: {query}", state="complete")
            if event.type == "raw_response_event":
                update_status(status_container, event.data.type)

                if event.data.type == "response.output_text.delta":
                    response += event.data.delta
                    text_placeholder.write(response)

                elif event.data.type == "response.image_generation_call.partial_image":
                    image = base64.b64decode(event.data.partial_image_b64)
                    image_placeholder.image(image)

prompt = st.chat_input("최근 고민이 무엇인가요?", accept_file=True, file_type=["txt"])

if prompt:
    # 사용자의 새로운 메세지가 입력되면 기존 placeholder 초기화
    if "image_placeholder" in st.session_state:
        st.session_state["image_placeholder"].empty()
    if "text_placeholder" in st.session_state:
        st.session_state["text_placeholder"].empty()

    for file in prompt.files:
        if file.type.startswith("text/"):
            with st.chat_message("ai"):
                with st.status("⏳ 파일 업로드 중...") as status:
                    uploaded_file = client.files.create(
                        file=(file.name, file.getvalue()),
                        purpose="user_data"
                    )
                    status.update(label="Attaching File...")
                    client.vector_stores.files.create(
                        vector_store_id=VECTOR_STORE_ID,
                        file_id=uploaded_file.id
                    )
                    status.update(label="✅ File uploaded", state="complete")
    if prompt.text:
        with st.chat_message("human"):
            st.write(prompt.text)
        asyncio.run(run_agent(prompt.text))

with st.sidebar:
    if "goals" in st.session_state:
        done, total = calc_progress(st.session_state["goals"])
        ratio = done / total if total > 0 else 0
        st.subheader("🎯 목표 진행률")
        st.progress(ratio, text=f"{done} / {total} 달성")

    reset = st.button("메모리 초기화")
    if reset:
        asyncio.run(session.clear_session())
    # st.write(asyncio.run(session.get_items()))