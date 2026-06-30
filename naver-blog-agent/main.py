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
    init_input = f"주제: {ctx.topic}\n경험 메모: {ctx.experience}"
    if ctx.highlights:
        init_input += f"\n강조점: {ctx.highlights}"

    with st.status("🔍 리서치 중...", expanded=False) as status:
        r1 = await Runner.run(research_agent, input=init_input, context=ctx)

        status.update(label="📝 글 구조 설계 중...")
        t_input = f"{r1.final_output}\n\n[작성자 경험 메모]: {ctx.experience}"
        r2 = await Runner.run(template_agent, input=t_input, context=ctx)

        status.update(label="✍️ 본문 집필 중...")
        w_input = f"{r2.final_output}\n\n[작성자 경험 메모]: {ctx.experience}"
        r3 = await Runner.run(writing_agent, input=w_input, context=ctx)

        status.update(label="✅ 완성!", state="complete")
    return r3.final_output


st.title("네이버 블로그 보조 에이전트")

topic = st.text_input("주제 / 제품명")
experience = st.text_area("경험 메모 (직접 겪은/써본 내용)")
highlights = st.text_input("강조하고 싶은 점 (선택)")
rating = st.slider("별점 (선택)", 1, 5, 5)

if st.button("초안 생성"):
    ctx = BlogContext(
        topic=topic, experience=experience, highlights=highlights or None, rating=rating
    )
    result = asyncio.run(run_pipeline(ctx))
    st.code(result)
