import asyncio
import os
import uuid

import streamlit as st

st.set_page_config(page_title="Restaurant Agent", page_icon="👨🏻‍🍳", layout="centered")

os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

from agents import (
    InputGuardrailTripwireTriggered,
    MaxTurnsExceeded,
    OutputGuardrailTripwireTriggered,
    Runner,
    SQLiteSession,
)
from models import RestaurantContext
from my_agents.triage_agent import triage_agent

if "ctx" not in st.session_state:
    st.session_state["ctx"] = RestaurantContext(customer_id=1, name="toma")
ctx = st.session_state["ctx"]

if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())

if "session" not in st.session_state:
    st.session_state["session"] = SQLiteSession(
        st.session_state["session_id"], "restaurant-order-memory.db"
    )
session = st.session_state["session"]

st.title("Tomato Kitchen")
st.caption("메뉴·주문·예약·문의를 도와드려요")


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
    return len(messages)


history_count = asyncio.run(paint_history())
if history_count == 0:
    st.info("""
👨🏻‍🍳 어서오세요, Tomato Kitchen입니다!

🍽️ 메뉴 추천 · 📝 주문 · 📅 예약 · 🙇 문의를 도와드려요!
""")

AGENT_LABELS = {
    "Menu_Agent": ("🍽️", "메뉴 전문가"),
    "Order_Agent": ("📝", "주문 담당자"),
    "Reservation_Agent": ("📅", "예약 담당자"),
    "Complaints_Agent": ("🙇", "고객 지원 담당자"),
}


async def run_agent(message):
    with st.chat_message("assistant"):
        text_placeholder = st.empty()
        response = ""
        current_agent = triage_agent
        last_agent = st.session_state.get("last_agent")

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
                        icon, label = AGENT_LABELS.get(
                            event.new_agent.name, ("🤖", event.new_agent.name)
                        )

                        if event.new_agent.name != last_agent:
                            st.info(f"{icon} {label}에게 연결합니다...")

                        st.session_state["last_agent"] = event.new_agent.name
                        current_agent = event.new_agent
                        text_placeholder = st.empty()
                        response = ""

        except InputGuardrailTripwireTriggered:
            text_placeholder.write(
                "🍅 죄송해요, 저는 Tomato Kitchen의 메뉴·주문·예약·문의만 도와드릴 수 있어요."
            )

        except OutputGuardrailTripwireTriggered:
            text_placeholder.write(
                "🍅 죄송합니다, 지금은 답변을 도와드리기 어려워요. 메뉴·주문·예약·문의로 다시 요청해 주세요!"
            )

        except MaxTurnsExceeded:
            st.error("🍅 에이전트 연결이 반복되어 요청을 완료하지 못했습니다.")


message = st.chat_input(
    "🍅 메뉴 및 예약, 주문 내용을 입력해주세요.",
)

if message:
    with st.chat_message("user"):
        st.write(message)
    asyncio.run(run_agent(message))

with st.sidebar:
    st.markdown("### 👨🏻‍🍳 Tomato Kitchen")
    st.caption("상담 연결 내역")
    st.divider()

    logs = st.session_state.get("handoff_logs", [])

    if not logs:
        st.caption("아직 연결된 담당자가 없어요.")

    for order, log in reversed(list(enumerate(logs, start=1))):
        icon, label = AGENT_LABELS.get(
            log["to_agent"],
            ("🤖", log["to_agent"]),
        )

        with st.container(border=True):
            st.markdown(f"**{icon} {label}**  ·  `#{order}`")
            st.write(log["summary"])
            st.caption(f"이유: {log['reason']}")

    st.divider()
    if st.button("대화 초기화", use_container_width=True):
        asyncio.run(session.clear_session())
        st.session_state["handoff_logs"] = []
        st.session_state["last_agent"] = None
