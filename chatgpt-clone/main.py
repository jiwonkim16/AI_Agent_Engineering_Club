import dotenv

dotenv.load_dotenv()
from openai import OpenAI
import asyncio
import base64
import streamlit as st
from agents import Agent, Runner, SQLiteSession, WebSearchTool, FileSearchTool, ImageGenerationTool, CodeInterpreterTool, HostedMCPTool
from agents.mcp.server import MCPServerStdio

client = OpenAI()
# OpenAI Agent SDK에서는 Hosted Tools라는 것을 제공함.
# OpenAI에서 미리 정의해둔 내장 에이전트 도구이며, 이들은 내 컴퓨터가 아니라 OpenAI 서버에서 구동됨. (WebSearchTool, FileSearchTool 등등)

# ---

# FileSearchTool
# OpenAI에는 파일을 저장할 수 있는 스토리지가 있으며, agent는 유저가 질문할 때마다 그 스토리지에 들어가서 파일을 읽을 수 있음.
# 1. Vector Store 생성
VECTOR_STORE_ID = "vs_6a2ffc988cdc8191a8016140e04df2cb"
# 2. 파일 업로드 : `prompt = st.chat_input("Write a message for your assistant", accept_file=True, file_type=["txt"])`
# 3. 스토리지 저장 : `if prompt:` 아래 확인.
# 4. 스토리지에 저장한 파일들을 에이전트가 연결된 vector store로 넣어주어야 함.

# ---

# 멀티모달 : 에이전트가 텍스트 뿐만 아니라 이미지 같은 것도 처리, 내장된 기능이기 때문에 별도 tool 불필요
# 이미지를 base64로 인코딩해서 메모리에 추가하면 됨.(이미지를 하나의 거대한 문자열로 인코딩)

# ---

# ImageGenerationTool
# 이미지 생성 툴, tool_config 필요.
# 에이전트에 이미지 생성 요청 시 이벤트를 받음.
# tool_config에 particial_image 설정을 추가하면 이벤트와 함께 받을 수 있음.
# 빈 이미지 placeholder 생성,

# ---

# CodeInterpreterTool
# LLM이 내 컴퓨터와 격리된 별도 환경인 샌드박스 환경에서 코드를 실행.
# AI가 질문에 답하기 위해 코드를 작성하고 실행해야 할 때 동작함.

# ---

# MCP
# HostedMCPTool : OpenAI의 서버에서 실행되며, 원격의 MCP 서버를 호출
#  - URL만 알면 됨.
# MCPServerStdio : 로컬에서 돌아가는 MCP 서버를 추가하는 것, stdio 발음은 스탠다드io
#  - from agents.mcp.server import MCPServerStdio 로 import
#  - 로컬에서 실행하기 위한 명령어가 필요.
#    - "yahoo-finance": {
#         "command": "uvx",
#         "args": ["mcp-yahoo-finance"]
#       }
#  - uvx란 npx와 같이 설치 없이 바로 실행하는 것 / uv와 npm은 설치 후 실행

# ---

# app 실행 후 한번만 에이전트 생성
if "agent" not in st.session_state:
    
    # 에이전트 생성 시 우선 로컬 MCP 서버가 실행되도록 해야 함.
    # 이렇게 로컬 mcp를 사용하는 경우 위와 같은 캐싱을 사용할 수 없음. 왜냐하면 서버를 계속 실행되게 해두고 agent를 만들 때 실행 중인 서버를 넘겨주어야 하기 때문.
    # 
    # yfinance_server = MCPServerStdio(
    #     params={
    #         "command": "uvx",
    #         "args": ["mcp-yahoo-finance"]
    #     }
    # )

    st.session_state["agent"] = Agent(
        # 로컬 mcp 서버 명시, 여러 mcp 서버를 연결 할땐 아래 배열에 추가만 해주면 됨.
        # mcp_servers=[yfinance_server]
        name="ChatGPT Clone",
        instructions="""
        You are a helpful assistant.

        You have access to the following tools:
          - Web Search Tool: Use this when the user asks a questions that isn't in your training data.
            Use this to learn about current events.
          - File Search Tool: Use this tool when the user asks a question about facts related to themselves.
            Or when they ask questions about specific files.
          - Code Interpreter Tool: Use this tool when you need write and run code to answer the user's question.
        """,
        tools=[
            WebSearchTool(),
            FileSearchTool(
                vector_store_ids=[VECTOR_STORE_ID],  # 사용자마다 각각의 vector store를 만들 수 있음.
                max_num_results=3,  # 스토어의 파일 중 상위 3개 파일만 가져옴.
            ),
            ImageGenerationTool(
                tool_config={
                    "type": "image_generation", # 필수 옵션
                    "quality": "medium",  # 생성 이미지 품질
                    "output_format": "jpeg",  # 이미지 확장자
                    "moderation": "low",
                    "partial_images": 1  # 이미지 생성 과정
                }
            ),
            CodeInterpreterTool(
                tool_config={
                    "type": "code_interpreter",  # 필수 옵션
                    "container": {
                        "type": "auto",
                        # "file_ids": [""]   스토리지에 업로드한 file id를 명시해서 모델이 코드를 작성할 때, 파일에 접근할 수 있는 권한을 줌.
                    }
                }
            ),
            HostedMCPTool(
                tool_config={
                    "server_url": "https://mcp.context7.com/mcp",
                    "type": "mcp",
                    "server_label": "Context_7",
                    "server_description": "Use this to get the docs from software projects.",
                    "require_approval": "never"  # mcp 사용 전 승인단계 해제
                }
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
                    content = message["content"]
                    # content가 문자열이면
                    if isinstance(content, str):
                        st.write(content)
                    # content가 list이면
                    elif isinstance(content, list):
                        for part in content:
                            if "image_url" in part:
                                st.image(part["image_url"])
                else:
                    if message["type"] == "message":
                        st.write(message["content"][0]["text"].replace("$", "\$"))
        if "type" in message:
            message_type = message["type"]
            if message_type == "web_search_call":
                with st.chat_message('ai'):
                    st.write("🚀 Search the Web...")
            elif message_type == "file_search_call":
                with st.chat_message("ai"):
                    st.write("📃 Searched your files...")
            # 이미지 생성 history 처리
            elif message_type == "image_generation_call":
                image = base64.b64decode(message["result"])
                with st.chat_message("ai"):
                    st.image(image)
            # 실행 코드
            elif message_type == "code_interpreter_call":
                with st.chat_message("ai"):
                    st.code(message["code"])
            elif message_type == "mcp_list_tools":
                with st.chat_message("ai"):
                    st.write(f"Listed {message["server_label"]}'s Tools")
            elif message_type == "mcp_call":
                with st.chat_message("ai"):
                    st.write(f"Called {message["server_label"]}'s {message["name"]}")


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
        'response.file_search_call.searching': ("⏳ File search in progress... ", "running"),
        'response.image_generation_call.generating': ("🎨 Drawing image...", "running"),
        'response.image_generation_call.in_progress': ("🎨 Drawing image...", "running"),
        'response.code_interpreter_call_code.done': ("🧑🏻‍💻 Ran code.", "complete"),
        'response.code_interpreter_call.completed': ("🧑🏻‍💻 Ran code.", "complete"),
        'response.code_interpreter_call.in_progress': ("🧑🏻‍💻 Running code.", "running"),
        'response.code_interpreter_call.interpreting': ("🧑🏻‍💻 Running code.", "running"),
        "response.mcp_call.completed": ("⚒️ Called MCP tool", "complete"),
        "response.mcp_call.failed": ("⚒️ Error calling MCP tool", "complete"),
        "response.mcp_call.in_progress": ("⚒️ Calling MCP tool...", "running"),
        "response.mcp_list_tools.completed": ("⚒️ Listed MCP tools", "complete"),
        "response.mcp_list_tools.failed": ("⚒️ Error listing MCP tools", "complete"),
        "response.mcp_list_tools.in_progress": ("⚒️ Listing MCP tools", "running"),
        'response.completed': (" ", "complete")

    }

    if event in status_messages:
        label, state = status_messages[event]
        status_container.update(label=label, state=state)

# Runner 실행 함수
async def run_agent(message):
    with st.chat_message("ai"):
        status_container = st.status("⏳", expanded=False)
        # AI 답변을 위한 컨테이너를 delta로 채워서 GPT와 같이 응답하도록.(delta는 생성과정을 모두 보여줌. 안 / 녕하 / 세 / 요. 와 같은 식, 이를 하나의 공간에 담기위함.)
        code_placeholder = st.empty()
        image_placeholder = st.empty()
        text_placeholder = st.empty()
        response = ""
        code_response = ""

        # 유저가 새로운 메세지를 보낼 때만 컨테이너를 비워주고 싶음.
        # 이를 위해 placeholder들을 session에 캐싱
        st.session_state["code_placeholder"] = code_placeholder
        st.session_state["image_placeholder"] = image_placeholder
        st.session_state["text_placeholder"] = text_placeholder

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

                # delta는 모델이 코드를 작성하고 있는 상태.
                if event.data.type == "response.code_interpreter_call_code.delta":
                    code_response += event.data.delta
                    # code 라는 메서드는 단순히 텍스트만 그리는게 아니라 syntax highlight가 적용된 code를 보여주는 streamlit 메서드
                    code_placeholder.code(code_response)

                # Image Generate Event
                elif event.data.type == "response.image_generation_call.partial_image":
                    # 이미지 생성 시 base64로 받기 때문에 디코딩 과정이 필요.
                    image = base64.b64decode(event.data.partial_image_b64)
                    image_placeholder.image(image)

            # tool_called 이벤트는 모든 종류의 툴 호출에서 발생.
            # raw_item의 클래스가 툴마다 다름. 예를 들어 FileSearchTool에는 action 속성이 없음.
            if event.type == "run_item_stream_event":
                if event.name == "tool_called":
                    if hasattr(event.item.raw_item, "action"):
                        query = event.item.raw_item.action.query
                        status_container.update(label=f"🔍 웹 검색: {query}", state="running")

prompt = st.chat_input(
    "Write a message for your assistant",
    accept_file=True,
    file_type=["txt", "jpg", "jpeg", "png"]
)

# streamlit에선 interaction이 발생할 때마다 전체가 리렌더링
if prompt:
    # 사용자의 새로운 메세지가 입력되면 기존 placeholder 초기화
    if "code_placeholder" in st.session_state:
        st.session_state["code_placeholder"].empty()
    if "image_placeholder" in st.session_state:
        st.session_state["image_placeholder"].empty()
    if "text_placeholder" in st.session_state:
        st.session_state["text_placeholder"].empty()

    # text 뿐만 아니라 파일도 받으므로 ..
    for file in prompt.files:
        if file.type.startswith("text/"):
            with st.chat_message("ai"):
                with st.status("⏳ Uploading file...") as status:
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
                    status.update(label="✅ File uploaded", state="complete")
        # 이미지 업로드
        elif file.type.startswith("image/"):
            with st.status("⏳ Uploading image...") as status:
                file_bytes = file.getvalue()
                # image encoding
                base64_data = base64.b64encode(file_bytes).decode("utf-8")
                # AI Model를 위한 URI 생성
                data_uri = f"data:{file.type};base64,{base64_data}"
                # 메모리에 이미지 추가
                asyncio.run(
                    session.add_items(
                        [
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "input_image",
                                        "detail": "auto",
                                        "image_url": data_uri
                                    }
                                ]
                            }
                        ]
                    )
                )
                status.update(label="✅ Image uploaded", state="complete")
            # 사용자에게 업로드된 이미지를 보여줌
            with st.chat_message("human"):
                st.image(data_uri)

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
