from pydantic import BaseModel


class OrderItem(BaseModel):
    name: str
    quantity: int


class RestaurantContext(BaseModel):
    customer_id: int
    name: str
    order: list[OrderItem] = []


class InputGuardRailOutput(BaseModel):
    is_off_topic: bool
    reason: str


class OutputGuardRailOutput(BaseModel):
    reveals_internal_info: bool
    is_unprofessional: bool
    reason: str


class HandoffData(BaseModel):
    reason: str
    summary: str
