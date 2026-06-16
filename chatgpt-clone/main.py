import dotenv

dotenv.load_dotenv()
from openai import OpenAI
import asyncio
import streamlit as st
from agents import Agent, Runner, SQLiteSession, WebSearchTool, FileSearchTool

client = OpenAI()

VECTOR_STORE_ID = "vs_6a2ffc988cdc8191a8016140e04df2cb"

if "agent" not in st.session_state:
    st.session_state["agent"] = Agent(
        name="Life Coach Agent",
        instructions="""
        너는 Life Coach Assistant야.
        사용자의 질문에 맞춰 동기부여 콘텐츠, 자기 개발 팁, 습관 형성 조언을 무조건 아래 도구를 활용해서 응답해줘.

        - Web Search Tool : 이 툴을 사용하여 개인화된 추천을 제공하고 사용자 질문에 관련된 정보를 검색
        - File Search Tool : Use this tool when the user asks a question about facts related to themselves. Or when they ask questions about specific
        """,
        tools=[
            WebSearchTool(),
            FileSearchTool(
                vector_store_ids=[VECTOR_STORE_ID],
                max_num_results=3
            )
        ]
    )

agent = st.session_state["agent"]

if "session" not in st.session_state:
    st.session_state["session"] = SQLiteSession("chat-history", "life-coach-memory.db")

session = st.session_state["session"]

async def paint_history():
    messages = await session.get_items()

    for message in messages:
        if "role" in message:
            with st.chat_message(message["role"]):
                if message["role"] == "user":
                    st.write(message["content"])
                else:
                    if message["type"] == "message":
                        st.write(message["content"][0]["text"])
        if "type" in message:
            if message["type"] == "web_search_call":
                with st.chat_message("ai"):
                    st.write("🚀 웹 검색 ...")
            elif message["type"] == "file_search_call":
                with st.chat_message("ai"):
                    st.write("📂 파일 검색 ...")

asyncio.run(paint_history())

def update_status(status_container, event):
    status_messages = {
        'response.web_search_call.completed': ("✅ 웹 검색 완료", "complete"),
        'response.web_search_call.in_progress': ("🤖 웹 검색 시작...", "running"),
        'response.web_search_call.searching': ("⏳ 웹 검색 중... ", "running"),
        'response.file_search_call.completed': ("✅ 파일 검색 완료", "complete"),
        'response.file_search_call.in_progress': ("📃 파일 검색 시작...", "running"),
        'response.file_search_call.searching': ("⏳ 파일 검색 중... ", "running"),
        'response.completed': (" ", "complete")
    }

    if event in status_messages:
        label, state = status_messages[event]
        status_container.update(label=label, state=state)

async def run_agent(message):
    with st.chat_message("ai"):
        status_container = st.status("🌿", expanded=False)
        text_placeholder = st.empty()
        response = ""

        stream = Runner.run_streamed(
            agent,
            message,
            session=session
        )

        async for event in stream.stream_events():
            if event.type == "run_item_stream_event":
                if event.name == "tool_called":
                    if hasattr(event.item.raw_item, "action"):
                        query = event.item.raw_item.action.query
                        status_container.update(label=f"🔍 웹 검색: {query}", state="complete")
            if event.type == "raw_response_event":
                update_status(status_container, event.data.type)

                if event.data.type == "response.output_text.delta":
                    response += event.data.delta
                    text_placeholder.write(response)

prompt = st.chat_input("최근 고민이 무엇인가요?", accept_file=True, file_type=["txt"])

if prompt:
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
    reset = st.button("메모리 초기화")
    if reset:
        asyncio.run(session.clear_session())
    st.write(asyncio.run(session.get_items()))