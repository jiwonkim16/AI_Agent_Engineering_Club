import streamlit as st
import time

st.write("Hello world")

st.button("Click me Please")

st.text_input("Write your API KEY", max_chars=20)

st.feedback("faces")

with st.sidebar:
    # with -> 영역 구분, 이 아래 위젯들은 모두 sidebar 영역에 속함
    st.badge("Badge 1")

tab1, tab2, tab3 = st.tabs(["Agent", "Chat", "Output"])

with tab1:
    st.header("Agent")
with tab2:
    st.header("Agent2")
with tab3:
    st.header("Agent3")

with st.chat_message("ai"):
    st.text("Hello")
    with st.status("Agent is using Tool") as status:
        time.sleep(1)
        status.update(label="Agent is searching the Web ...")
        time.sleep(2)
        status.update(label="Agent is reading the Page")
        time.sleep(3)
        status.update(state="complete")
        
with st.chat_message("human"):
    st.text("Hi!")

st.chat_input("Write a message for the assistant.", accept_file=True)