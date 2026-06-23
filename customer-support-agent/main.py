import dotenv

dotenv.load_dotenv()
import asyncio

import streamlit as st
from agents import (
    InputGuardrailTripwireTriggered,
    MaxTurnsExceeded,
    Runner,
    SQLiteSession,
)
from openai import OpenAI

from models import RestaurantContext
from my_agents.triage_agent import triage_agent

client = OpenAI()

if "ctx" not in st.session_state:
    st.session_state["ctx"] = RestaurantContext(customer_id=1, name="toma")
ctx = st.session_state["ctx"]

if "session" not in st.session_state:
    st.session_state["session"] = SQLiteSession(
        "chat-history", "restaurant-order-memory.db"
    )
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
                        st.write(message["content"][0]["text"].replace("$", r"\$"))


asyncio.run(paint_history())


async def run_agent(message):
    with st.chat_message("ai"):
        text_placeholder = st.empty()
        response = ""
        current_agent = triage_agent

        st.session_state["text_placeholder"] = text_placeholder

        try:
            stream = Runner.run_streamed(
                triage_agent, message, session=session, context=ctx, max_turns=4
            )

            async for event in stream.stream_events():
                if event.type == "raw_response_event":
                    if event.data.type == "response.output_text.delta":
                        response += event.data.delta
                        text_placeholder.write(response.replace("$", r"\$"))

                elif event.type == "agent_updated_stream_event":
                    if current_agent.name != event.new_agent.name:
                        display_name = {
                            "Menu_Agent": "메뉴 전문가",
                            "Order_Agent": "주문 담당자",
                            "Reservation_Agent": "예약 담당자",
                        }.get(event.new_agent.name, event.new_agent.name)

                        st.info(f"{display_name}에게 연결합니다...")
                        current_agent = event.new_agent
                        text_placeholder = st.empty()
                        response = ""

        except InputGuardrailTripwireTriggered:
            st.write("저는 그 부분에 대해 도움을 드릴 수 없습니다.")

        except MaxTurnsExceeded:
            st.error("에이전트 연결이 반복되어 요청을 완료하지 못했습니다.")


message = st.chat_input(
    "메뉴 및 예약, 주문 내용을 입력해주세요.",
)

if message:
    if "text_placeholder" in st.session_state:
        st.session_state["text_placeholder"].empty()

    if message:
        with st.chat_message("human"):
            st.write(message)
        asyncio.run(run_agent(message))

AGENT_LABELS = {
    "Menu_Agent": ("🍽️", "메뉴 전문가"),
    "Order_Agent": ("📝", "주문 담당자"),
    "Reservation_Agent": ("📅", "예약 담당자"),
}

with st.sidebar:
    st.subheader("Agent Handoffs")

    logs = st.session_state.get("handoff_logs", [])

    if not logs:
        st.caption("아직 handoff 기록이 없습니다.")

    for log in reversed(logs):
        icon, label = AGENT_LABELS.get(
            log["to_agent"],
            ("🤖", log["to_agent"]),
        )

        with st.container(border=True):
            st.markdown(f"### {icon} {label}")
            st.write(log["summary"])
            st.caption(f"이유: {log['reason']}")

    if st.button("Reset memory"):
        asyncio.run(session.clear_session())
        st.session_state["handoff_logs"] = []

    with st.expander("Raw memory"):
        st.write(asyncio.run(session.get_items()))
