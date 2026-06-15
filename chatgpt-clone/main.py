import dotenv

dotenv.load_dotenv()
import asyncio
import streamlit as st
from agents import Agent, Runner, SQLiteSession, WebSearchTool

if "agent" not in st.session_state:
    st.session_state["agent"] = Agent(
        name="Life Coach Agent",
        instructions="""
        너는 Life Coach Assistant야.
        사용자의 질문에 맞춰 동기부여 콘텐츠, 자기 개발 팁, 습관 형성 조언을 무조건 아래 도구를 활용해서 응답해줘.

        - Web Search Tool
        """,
        tools=[WebSearchTool()]
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

asyncio.run(paint_history())

def update_status(status_container, event):
    status_messages = {
        'response.web_search_call.completed': ("✅ 웹 검색 완료", "complete"),
        'response.web_search_call.in_progress': ("🤖 웹 검색 시작...", "running"),
        'response.web_search_call.searching': ("⏳ 웹 검색 중... ", "running"),
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
                    query = event.item.raw_item.action.query
                    status_container.update(label=f"🔍 웹 검색: {query}", state="complete")
            if event.type == "raw_response_event":
                update_status(status_container, event.data.type)

                if event.data.type == "response.output_text.delta":
                    response += event.data.delta
                    text_placeholder.write(response)

prompt = st.chat_input("최근 고민이 무엇인가요?")

if prompt:
    with st.chat_message("human"):
        st.write(prompt)
    asyncio.run(run_agent(prompt))

with st.sidebar:
    reset = st.button("메모리 초기화")
    if reset:
        asyncio.run(session.clear_session())
    st.write(asyncio.run(session.get_items()))