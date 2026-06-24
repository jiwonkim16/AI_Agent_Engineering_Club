# __init__.py 파일을 폴더에 추가하면 해당 폴더는 파이썬 패키지가 되고 __init__.py 파일은 패키지의 진입점이 됨.
# 패키지의 진입 지점에서 agent를 export
# 그래서 Google ADK는 항상 root_agent라는 변수를 찾게 되어 있음.
# 그러므로 ADK가 financial advisor 패키지로 들어오면 __init__ 파일을 찾고 이를 통해 root_agent 변수가 있는 agent 모듈 파일을 찾음.

from . import agent
