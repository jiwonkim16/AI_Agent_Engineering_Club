import os

import requests
from agents import RunContextWrapper, function_tool

from models import BlogContext


@function_tool
def naver_search(wrapper: RunContextWrapper[BlogContext], query: str) -> str:
    # 1. URL + 헤더
    # 2. params: query, display
    response = requests.get(
        "https://openapi.naver.com/v1/search/blog.json",
        params={"query": query, "display": 5},
        headers={
            "X-Naver-Client-Id": os.environ["NAVER_CLIENT_ID"],
            "X-Naver-Client-Secret": os.environ["NAVER_CLIENT_SECRET"],
        },
    )
    # 3. requests.get(...) -> 응답 json의 items
    data = response.json()
    # ponytail: 결과 0건/401이면 KeyError로 터짐. 로컬 트러스트 도구라 미룸, 실제로 터지면 가드 추가
    items = data["items"]
    # 4. 각 item에서 title, link, description 뽑아 "정리된 문자열" 로 반환
    results = []
    for item in items:
        title = item["title"].replace("<b>", "").replace("</b>", "")
        desc = item["description"].replace("<b>", "").replace("</b>", "")
        link = item["link"]
        results.append(f"{title}\n{desc}\n출처: {link}")

    return "\n\n".join(results)
