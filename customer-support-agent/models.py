from pydantic import BaseModel

# 유저 계정 context를 위한 BaseModel
class UserAccountContext(BaseModel):

    customer_id: int
    name: str
    tier: str = "basic"

# 에이전트 -> 구조회된 답변
class InputGuardRailOutput(BaseModel):

    is_off_topic: bool
    reason: str