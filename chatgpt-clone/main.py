import dotenv

dotenv.load_dotenv()
from openai import OpenAI
import asyncio
import streamlit as st
from agents import Agent, Runner, SQLiteSession, WebSearchTool, FileSearchTool

client = OpenAI()
# OpenAI Agent SDK에서는 Hosted Tools라는 것을 제공함.
# OpenAI에서 미리 정의해둔 내장 에이전트 도구이며, 이들은 내 컴퓨터가 아니라 OpenAI 서버에서 구동됨. (WebSearchTool, FileSearchTool 등등)

# FileSearchTool
# OpenAI에는 파일을 저장할 수 있는 스토리지가 있으며, agent는 유저가 질문할 때마다 그 스토리지에 들어가서 파일을 읽을 수 있음.
# 1. Vector Store 생성
VECTOR_STORE_ID = "vs_6a2ffc988cdc8191a8016140e04df2cb"
# 2. 파일 업로드 : `prompt = st.chat_input("Write a message for your assistant", accept_file=True, file_type=["txt"])`
# 3. 스토리지 저장 : `if prompt:` 아래 확인.
# 4. 스토리지에 저장한 파일들을 에이전트가 연결된 vector store로 넣어주어야 함. 

# app 실행 후 한번만 에이전트 생성
if "agent" not in st.session_state:
    st.session_state["agent"] = Agent(
        name="ChatGPT Clone",
        instructions="""
        You are a helpful assistant.

        You have access to the following tools:
          - Web Search Tool: Use this when the user asks a questions that isn't in your training data.
            Use this to learn about current events.
          - File Search Tool: Use this tool when the user asks a question about facts related to themselves.
            Or when they ask questions about specific files.
        """,
        tools=[
            WebSearchTool(),
            FileSearchTool(
                vector_store_ids=[VECTOR_STORE_ID],  # 사용자마다 각각의 vector store를 만들 수 있음.
                max_num_results=3,  # 스토어의 파일 중 상위 3개 파일만 가져옴.
            )
        ]
    )

# 위 조건문 안에 있으면 agent가 session_state에 없을 때만 실행되고 이후부터는 undefined가 되므로 블록 바깥에서 실행.
agent = st.session_state["agent"]

# 앱 실행 후 한번만 session 초기화
if "session" not in st.session_state:
    st.session_state["session"] = SQLiteSession("chat-history", "chat-gpt-clone-memory.db")

# session이라는 변수명을 사용하기 위함.
session = st.session_state["session"]

# 메모리에 있는 content를 가져오는 비동기 함수
async def paint_history():
    messages = await session.get_items()

    for message in messages:
        if "role" in message:
            with st.chat_message(message["role"]):  # dict 이기 때문에 이와 같이 가져와야함. message.role (x)
                if message["role"] == "user":
                    st.write(message["content"])
                else:
                    if message["type"] == "message":
                        st.write(message["content"][0]["text"].replace("$", "\$"))
        if "type" in message:
            if message["type"] == "web_search_call":
                with st.chat_message('ai'):
                    st.write("🚀 Search the Web...")
            elif message["type"] == "file_search_call":
                with st.chat_message("ai"):
                    st.write("📃 Searched your files...")

# 메세지를 보내고 리렌더링 될때마다 대화 기록을 그리고 있기 때문에 이전 대화목록을 확인할 수 있음 (순서 중요.)
asyncio.run(paint_history())

# Streamlit의 status를 활용하여 이벤트 상태 UI 표시 및 업데이트
def update_status(status_container, event):
    # event.data.type 중 web search 와 관련된 타입들을 튜플 형태로 맵핑
    status_messages = {
        'response.web_search_call.completed': ("✅ Web search completed.", "complete"),
        'response.web_search_call.in_progress': ("🤖 Starting web search...", "running"),
        'response.web_search_call.searching': ("⏳ Web search in progress... ", "running"),
        'response.file_search_call.completed': ("✅ File search completed.", "complete"),
        'response.file_search_call.in_progress': ("📃 Starting file search...", "running"),
        'response.file_search_call.searching': ("⏳ File search in progress... ", "running")
    }

    if event in status_messages:
        label, state = status_messages[event]
        status_container.update(label=label, state=state)

# Runner 실행 함수
async def run_agent(message):
    with st.chat_message("ai"):
        status_container = st.status("⏳", expanded=False)
        # AI 답변을 위한 컨테이너를 delta로 채워서 GPT와 같이 응답하도록.
        text_placeholder = st.empty()
        response = ""

        stream = Runner.run_streamed(
            agent,
            message,
            session=session
        )
        # streaming
        async for event in stream.stream_events():
            if event.type == "raw_response_event":

                update_status(status_container, event.data.type)

                if event.data.type == "response.output_text.delta":
                    response += event.data.delta
                    text_placeholder.write(response.replace("$", "\$"))

prompt = st.chat_input(
    "Write a message for your assistant",
    accept_file=True,
    file_type=["txt"]
)

# streamlit에선 interaction이 발생할 때마다 전체가 리렌더링
if prompt:
    # text 뿐만 아니라 파일도 받으므로 ..
    for file in prompt.files:
        if file.type.startswith("text/"):
            with st.chat_message("ai"):
                with st.status("Uploading file...") as status:
                    # 파일 업로드하면 OpenAI 스토리지에 저장
                    uploaded_file = client.files.create(
                        file=(file.name, file.getvalue()),
                        purpose="user_data"  # purpose 종류가 매우 많음. 중요.
                    )
                    status.update(label="Attaching file...")
                    client.vector_stores.files.create(
                        vector_store_id=VECTOR_STORE_ID,
                        file_id=uploaded_file.id
                    )
                    status.update(label="File uploaded", state="complete")

    if prompt.text:
        with st.chat_message("human"):
            st.write(prompt.text)
        # Runner에 prompt를 담아서 실행
        asyncio.run(run_agent(prompt.text)) 

# 메모리 삭제 버튼
# session.get_items()는 corutine 이기 때문에 await 키워드를 사용해야 하는데 
# async 함수 밖이라 await를 사용할 수 없음.
# 이런 경우 asyncio.run() 을 사용하면 await 와 같은 역할을 함.
with st.sidebar:
    reset = st.button("Reset Memory")
    if reset:
        asyncio.run(session.clear_session())
    st.write(asyncio.run(session.get_items()))
