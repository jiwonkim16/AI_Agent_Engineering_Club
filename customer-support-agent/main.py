import dotenv

dotenv.load_dotenv()
from openai import OpenAI
import asyncio
import streamlit as st
from agents import InputGuardrailTripwireTriggered, Runner, SQLiteSession, OutputGuardrailTripwireTriggered
from models import UserAccountContext
from my_agents.triage_agent import triage_agent


# Runner에서 사용된 context는 모든 function_tool의 첫번째 arg로 들어옴. 아래는 예시.
# @function_tool
# def get_user_tier(wrapper: RunContextWrapper[UserAccountContext]):

#     return (
#         f"The user {wrapper.context.customer_id} has a {wrapper.context.tier} account."
#     )


client = OpenAI()

# context 인스턴스
user_account_ctx = UserAccountContext(
    customer_id=1,
    name="toma",
    tier="basic",
)


if "session" not in st.session_state:
    st.session_state["session"] = SQLiteSession(
        "chat-history",
        "customer-support-memory.db",
    )
session = st.session_state["session"]

if "agent" not in st.session_state:
    st.session_state["agent"] = triage_agent

async def paint_history():
    messages = await session.get_items()
    for message in messages:
        if "role" in message:
            with st.chat_message(message["role"]):
                if message["role"] == "user":
                    st.write(message["content"])
                else:
                    if message["type"] == "message":
                        st.write(message["content"][0]["text"].replace("$", "\$"))


asyncio.run(paint_history())


async def run_agent(message):

    with st.chat_message("ai"):
        text_placeholder = st.empty()
        response = ""

        st.session_state["text_placeholder"] = text_placeholder

        try:
            stream = Runner.run_streamed(
                st.session_state["agent"],
                message,
                session=session,
                context=user_account_ctx,  # context 인스턴스를 Runner에서 사용. 자동으로 에이전트에게 전달되는 것은 아님. 이제 모든 function_tool들이 context를 다 받게 됨.
            )

            async for event in stream.stream_events():
                if event.type == "raw_response_event":

                    if event.data.type == "response.output_text.delta":
                        response += event.data.delta
                        text_placeholder.write(response.replace("$", "\$"))

                elif event.type == "agent_updated_stream_event":
                    if st.session_state["agent"].name != event.new_agent.name:
                        st.write(f"🤖 Transfered from {st.session_state["agent"].name} to {event.new_agent.name}")
                        st.session_state["agent"] = event.new_agent
                        text_placeholder = st.empty()
                        response = ""

        # 입력 가드레일 예외 발생 처리                
        except InputGuardrailTripwireTriggered:
            st.write("I can't help you with that.")

        # 출력 가드레일 예외
        except OutputGuardrailTripwireTriggered:
            st.write("Cant show you that answer.")
            st.session_state["text_placeholder"].empty()


message = st.chat_input(
    "Write a message for your assistant",
)

if message:

    if "text_placeholder" in st.session_state:
        st.session_state["text_placeholder"].empty()

    if message:
        with st.chat_message("human"):
            st.write(message)
        asyncio.run(run_agent(message))


with st.sidebar:
    reset = st.button("Reset memory")
    if reset:
        asyncio.run(session.clear_session())
    st.write(asyncio.run(session.get_items()))