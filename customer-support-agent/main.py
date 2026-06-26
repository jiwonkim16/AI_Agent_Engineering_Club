import asyncio
import os
import uuid

import streamlit as st

st.set_page_config(page_title="Tomato Kitchen", page_icon="🍅", layout="centered")

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
    st.session_state["ctx"] = RestaurantContext(customer_id=1, name="")
ctx = st.session_state["ctx"]

if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())

if "session" not in st.session_state:
    st.session_state["session"] = SQLiteSession(
        st.session_state["session_id"], "restaurant-order-memory.db"
    )
session = st.session_state["session"]

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800;900&family=Nunito:wght@400;600;700&display=swap');

    /* 강렬한 토마토 배경: 따뜻한 베이스 + 선명한 토마토 도트 */
    [data-testid="stAppViewContainer"] {
        background-color: #FCEAD9;
        background-image: radial-gradient(#E8704F 1px, transparent 1.2px);
        background-size: 20px 20px;
    }

    /* 본문 폰트 */
    html, body, [class*="st-"] { font-family: 'Nunito', sans-serif; }

    /* 타이틀: 굵은 serif + 강렬한 토마토 레드 */
    h1 {
        font-family: 'Playfair Display', serif !important;
        font-weight: 900 !important;
        color: #C0241B;
        letter-spacing: 0.5px;
    }
    h2, h3 { font-family: 'Playfair Display', serif !important; color: #C0241B; }

    /* 채팅 버블 공통: 흰 카드 + 굵은 토마토 레드 왼쪽 바 */
    [data-testid="stChatMessage"] {
        background-color: #FFFFFF;
        border-left: 6px solid #C0241B;
        border-radius: 14px;
        padding: 0.8rem 1.1rem;
        margin-bottom: 0.7rem;
        box-shadow: 0 3px 12px rgba(192, 36, 27, 0.12);
    }

    /* 입력창: 토마토 레드 테두리 강조 */
    [data-testid="stChatInput"] {
        border: 2px solid #C0241B;
        border-radius: 12px;
    }
    [data-testid="stChatInput"]:focus-within {
        box-shadow: 0 0 0 3px rgba(192, 36, 27, 0.2);
    }

    /* 환영/안내 info 박스: 토마토 톤 */
    [data-testid="stAlertContainer"] {
        background-color: #FFF3EC;
        border-left: 6px solid #E8704F;
    }

    /* 사이드바: 따뜻한 베이지 + 우측 토마토 라인 */
    [data-testid="stSidebar"] {
        background-color: #F6E3CF;
        border-right: 3px solid #C0241B;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🍅 Tomato Kitchen")
st.caption("토마토 전문 트라토리아 · 메뉴·주문·예약·문의를 도와드려요")

# 이름 게이트: 성함을 받기 전에는 채팅을 열지 않는다 (트라토리아 입구에서 호스트가 맞이하는 흐름).
if not ctx.name:
    st.info(
        "👨🏻‍🍳 Benvenuti! 토마토 전문 트라토리아 Tomato Kitchen입니다.\n\n먼저 성함을 알려주시면 정성껏 모시겠습니다!"
    )
    with st.form("name_gate"):
        name_input = st.text_input("성함", placeholder="예: 지원")
        submitted = st.form_submit_button("입장하기", use_container_width=True)
    if submitted and name_input.strip():
        ctx.name = name_input.strip()
        st.rerun()
    st.stop()


async def paint_history():
    messages = await session.get_items()
    for message in messages:
        if "role" in message:
            avatar = "🍅" if message["role"] == "assistant" else "🍽️"
            with st.chat_message(message["role"], avatar=avatar):
                if message["role"] == "user":
                    st.write(message["content"])
                else:
                    if message["type"] == "message":
                        st.write(message["content"][0]["text"].replace("$", r"\$"))
    return len(messages)


AGENT_LABELS = {
    "Menu_Agent": ("🍽️", "메뉴 전문가"),
    "Order_Agent": ("📝", "주문 담당자"),
    "Reservation_Agent": ("📅", "예약 담당자"),
    "Complaints_Agent": ("🙇", "고객 지원 담당자"),
}


async def run_agent(message):
    with st.chat_message("assistant", avatar="🍅"):
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
                "🍅 Mi dispiace! 저희 Tomato Kitchen은 메뉴·주문·예약·문의만 도와드릴 수 있어요."
            )

        except OutputGuardrailTripwireTriggered:
            text_placeholder.write(
                "🍅 Mi dispiace! 지금은 답변을 도와드리기 어려워요. 메뉴·주문·예약·문의로 다시 말씀해 주세요!"
            )

        except MaxTurnsExceeded:
            st.error(
                "🍅 담당자 연결이 반복되어 요청을 완료하지 못했어요. 다시 시도해 주세요!"
            )


@st.fragment
def chat_area():
    # 과거 대화 + 응답 생성을 fragment로 격리한다.
    # 응답 생성(느린 부분)이 fragment 안에 있어, 생성 중 과거 대화 전체가
    # 다시 그려지며 흐려지는 잔상(rerun-fade)이 사라진다.
    # chat_input은 fragment 밖(base level)에 있어야 하단 고정되므로,
    # 입력값은 session_state["pending_message"]로 전달받는다.
    history_count = asyncio.run(paint_history())
    if history_count == 0:
        st.info(f"""
👨🏻‍🍳 {ctx.name}님, 어서 오세요! Tomato Kitchen입니다.

🍅 저희는 토마토로 만든 요리만 정성껏 준비해요.

🍽️ 메뉴 추천 · 📝 주문 · 📅 예약 · 🙇 문의를 도와드릴게요!
""")

    pending = st.session_state.pop("pending_message", None)
    if pending:
        with st.chat_message("user", avatar="🍽️"):
            st.write(pending)
        asyncio.run(run_agent(pending))
        # 생성 완료 후 DB 기준으로 화면을 정리하고 사이드바(handoff 로그)도 갱신한다.
        # 이 rerun은 생성이 끝난 뒤라 빠르게 지나가 잔상을 만들지 않는다.
        st.rerun()


chat_area()

# chat_input은 base level에 둬야 화면 하단에 자동 고정된다.
# 입력을 pending에 담으면 chat_input 제출이 일으킨 rerun의 다음 패스에서
# 위 chat_area()가 이를 처리한다.
if prompt := st.chat_input("🍅 무엇을 도와드릴까요? (메뉴 · 주문 · 예약 · 문의)"):
    st.session_state["pending_message"] = prompt
    st.rerun()

with st.sidebar:
    st.markdown("### 🍅 Tomato Kitchen")

    logs = st.session_state.get("handoff_logs", [])

    # 지금 모시는 담당
    st.caption("지금 모시는 담당")
    if logs:
        cur_icon, cur_label = AGENT_LABELS.get(
            logs[-1]["to_agent"], ("🤖", logs[-1]["to_agent"])
        )
        st.markdown(f"## {cur_icon} {cur_label}")
    else:
        st.markdown("## 👨🏻‍🍳 호스트")
        st.caption("무엇을 도와드릴까요?")

    st.divider()
    st.caption("연결 내역")

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

    st.divider()
    if st.button("대화 초기화", use_container_width=True):
        asyncio.run(session.clear_session())
        st.session_state["handoff_logs"] = []
        st.session_state["last_agent"] = None
