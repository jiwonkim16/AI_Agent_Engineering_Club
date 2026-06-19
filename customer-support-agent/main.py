import dotenv

dotenv.load_dotenv()
from openai import OpenAI
import asyncio
import streamlit as st
from agents import Runner, SQLiteSession

client = OpenAI()

if "session" not in st.session_state:
    st.session_state["session"] = SQLiteSession("chat-history", "customer-support-memory.db")

session = st.session_state["session"]

if "agent" not in st.session_state:
    pass
    # st.session_state["agent"] = triage_agent

async def run_agent(message):
    with st.chat_message("ai"):
        status_container = st.status("⏳ Processing ...")

with st.sidebar:
    reset = st.button("Reset Memory")
    if reset:
        asyncio.run(session.clear_session())
    st.write(asyncio.run(session.get_items()))
