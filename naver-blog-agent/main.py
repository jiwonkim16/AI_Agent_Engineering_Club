import dotenv

dotenv.load_dotenv()

import asyncio

import streamlit as st
from agents import Runner

from models import BlogContext
from naver_blog_agents.research_agent import research_agent
from naver_blog_agents.template_agent import template_agent
from naver_blog_agents.writing_agent import writing_agent


async def run_pipeline(ctx: BlogContext) -> str:
    with st.status("🔍 리서치 중...", expanded=False) as status:
        r1 = await Runner.run(research_agent, input=f"주제: {ctx.topic}", context=ctx)
        st.markdown("**🔍 리서치 결과**")
        st.write(r1.final_output)

        status.update(label="📝 글 구조 설계 중...")
        r2 = await Runner.run(template_agent, input=r1.final_output, context=ctx)
        st.markdown("**📝 글 구조**")
        st.write(r2.final_output)

        status.update(label="✍️ 본문 집필 중...")
        r3 = await Runner.run(writing_agent, input=r2.final_output, context=ctx)

        status.update(label="✅ 완성!", state="complete")
    return r3.final_output


st.set_page_config(page_title="네이버 블로그 보조 에이전트", page_icon="📝", layout="centered")

st.title("📝 네이버 블로그 보조 에이전트")
st.caption("경험 메모를 남기면 리서치 → 구조 설계 → 집필까지 대신 해드려요.")

with st.container(border=True):
    st.subheader("1. 무엇에 대해 쓸까요?")
    topic = st.text_input("주제 / 제품명", placeholder="예: OO 기저귀 밴드형")
    experience = st.text_area(
        "경험 메모 (직접 겪은/써본 내용)",
        placeholder="언제, 어떻게 사용했는지 편하게 적어주세요.",
        height=140,
    )

    col1, col2 = st.columns([2, 1])
    with col1:
        highlights = st.text_input("강조하고 싶은 점 (선택)", placeholder="예: 흡수력, 가격")
    with col2:
        st.markdown("별점 (선택)")
        stars = st.feedback("stars")

    generate = st.button("✨ 초안 생성", type="primary", use_container_width=True)

if generate:
    if not topic or not experience:
        st.warning("주제와 경험 메모는 필수로 입력해주세요.")
    else:
        ctx = BlogContext(
            topic=topic,
            experience=experience,
            highlights=highlights or None,
            rating=stars + 1 if stars is not None else None,
        )
        st.session_state.result = asyncio.run(run_pipeline(ctx))

if "result" in st.session_state:
    st.subheader("2. 완성 초안")
    st.caption("아래 내용을 복사해서 네이버 블로그 에디터에 붙여넣으세요.")
    st.text_area("완성 초안", st.session_state.result, height=600, label_visibility="collapsed")
